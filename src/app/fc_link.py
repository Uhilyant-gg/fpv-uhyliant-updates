"""The flight controller wired to the camera: found by the station, its data brought over SSH.

Finding it (only while the drone is not armed): the station lists the camera's serial ports
(not the console), and on each tries the usual speeds for about a second, listening. A packet
with a correct checksum names the protocol:
- MAVLink (ArduPilot, PX4, INAV) - the flight controller sends it by itself;
- MSP (Betaflight, INAV) - it answers a short "which flight controller are you?" question;
- CRSF - its own frames.
The pilot can also set the port, speed and protocol by hand; "auto" is the default.

Bringing the data: the station reads that port through its own SSH session to the camera
(encrypted, on the station's networks only). Nothing is installed on the camera and no port is
opened on it, so nobody else can reach the flight controller or the camera through it. MAVLink
goes to the station's MAVLink reader on this PC (UDP 127.0.0.1), MSP and CRSF straight to theirs.
Only fixed commands built from a checked port name and a speed from a fixed list are sent.
"""

from __future__ import annotations

import json
import re
import socket
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from crsf_runtime import CrsfParser
from msp_runtime import MSP_FC_VARIANT, MspParser, build_request

BAUDS = (115200, 57600, 230400, 460800, 921600, 420000)
PROTOCOLS = ("MAVLink", "MSP", "CRSF")
PORT_RE = re.compile(r"^/dev/tty(?:AMA|S)\d{1,2}$")
LIST_COMMAND = "ls /dev/ttyAMA* /dev/ttyS* 2>/dev/null; echo ---; cat /proc/cmdline"
# "Which flight controller are you?" in MSP v1, written as octal for busybox printf.
MSP_ASK = "\\044\\115\\074\\000\\002\\002"
MAVLINK_LOCAL_PORT = 14550
# The readers the station left on the camera last time (a dropped SSH session may leave them running).
PID_FILE = "/tmp/fpv-uhyliant-fc.pid"
STOP_OLD = f"[ -f {PID_FILE} ] && kill $(cat {PID_FILE}) 2>/dev/null; rm -f {PID_FILE}"
VARIANTS = {"BTFL": "Betaflight", "INAV": "INAV", "ARDU": "ArduPilot", "EMUF": "EmuFlight"}
AUTOPILOTS = {3: "ArduPilot", 12: "PX4"}


def check_port(port: str) -> str:
    if not PORT_RE.match(str(port or "")):
        raise ValueError("port")
    return port


def check_baud(baud) -> int:
    if int(baud) not in BAUDS:
        raise ValueError("baud")
    return int(baud)


def parse_ports(text: str) -> list[str]:
    """Serial ports of the camera, without the one the camera's own console uses."""
    ports_part, _, cmdline = str(text or "").partition("---")
    console = re.search(r"console=(tty\w+)", cmdline)
    console_dev = f"/dev/{console.group(1)}" if console else ""
    ports = [p for p in ports_part.split() if PORT_RE.match(p) and p != console_dev]
    return sorted(set(ports), key=lambda p: (not p.startswith("/dev/ttyAMA"), p))


def stty(port: str, baud: int) -> str:
    return f"stty -F {check_port(port)} {check_baud(baud)} raw -echo -echoe -echok 2>/dev/null"


def sample_command(port: str, baud: int) -> str:
    """Listen for about a second; ask MSP once in the middle. Bytes come back as hex text."""
    port, baud = check_port(port), check_baud(baud)
    read = f"(timeout 1 cat {port} 2>/dev/null || timeout -t 1 cat {port} 2>/dev/null)"
    return (
        f"{STOP_OLD}; {stty(port, baud)} || exit 3; "
        f"(sleep 0.3; printf '{MSP_ASK}' > {port}) & {read} | head -c 2048 | od -An -v -tx1"
    )


def stream_command(port: str, baud: int) -> str:
    """Read the port for as long as the channel is open; what the station sends goes to the port."""
    port, baud = check_port(port), check_baud(baud)
    return (
        f"{STOP_OLD}; {stty(port, baud)} || exit 3; "
        f"exec 3<&0; cat <&3 > {port} & echo $! > {PID_FILE}; echo $$ >> {PID_FILE}; exec cat {port}"
    )


def parse_hex(text: str) -> bytes:
    return bytes(int(h, 16) for h in re.findall(r"\b[0-9a-fA-F]{2}\b", str(text or "")))


def identify(data: bytes) -> dict | None:
    """{protocol, detail} when the bytes hold valid packets of a known protocol."""
    if not data:
        return None
    try:
        from pymavlink.dialects.v20 import ardupilotmega as mavlink

        parser = mavlink.MAVLink(None)
        parser.robust_parsing = True
        messages = [m for m in (parser.parse_buffer(data) or []) if m.get_type() != "BAD_DATA"]
    except Exception:
        messages = []
    if len(messages) >= 2:
        beat = next((m for m in messages if m.get_type() == "HEARTBEAT"), None)
        return {"protocol": "MAVLink", "detail": AUTOPILOTS.get(getattr(beat, "autopilot", -1), "")}
    frames = [f for f in MspParser().feed(data) if f.direction == ">"]
    if frames:
        variant = next((f.payload[:4].decode("ascii", "ignore") for f in frames if f.command == MSP_FC_VARIANT), "")
        return {"protocol": "MSP", "detail": VARIANTS.get(variant, variant)}
    if len(CrsfParser().feed(data)) >= 2:
        return {"protocol": "CRSF", "detail": ""}
    return None


def detect(session, ports=None, bauds=BAUDS, wanted_protocol="") -> dict | None:
    """Try each port and speed; the first that speaks a known protocol wins."""
    if ports is None:
        _code, text = session.run(LIST_COMMAND)
        ports = parse_ports(text)
    for port in ports:
        for baud in bauds:
            code, text = session.run(sample_command(port, baud))
            if code == 3:
                continue  # this speed cannot be set on this port
            found = identify(parse_hex(text))
            if found and (not wanted_protocol or found["protocol"] == wanted_protocol):
                return {"port": port, "baud": baud, **found}
    return None


def link_text(link: dict) -> str:
    if not link:
        return ""
    port = link["port"].replace("/dev/", "")
    detail = f" · {link['detail']}" if link.get("detail") else ""
    return f"{link['protocol']} · порт {port} · {link['baud']}{detail}"


class FcLinkRuntime(QObject):
    """Finds the flight controller on the camera and brings its data to the station's readers."""

    changed = Signal()
    _detected = Signal(str, object)
    _data = Signal(int, bytes)
    _ended = Signal(int)

    def __init__(
        self,
        devices,
        connections,
        shell_for,
        store_path: Path,
        mavlink=None,
        msp=None,
        crsf=None,
        router=None,
        may_probe=lambda: True,
        run_async=True,
        clock=time.monotonic,
    ):
        super().__init__()
        self._devices = devices
        self._connections = connections
        self._shell_for = shell_for
        self._path = Path(store_path)
        self._mavlink, self._msp, self._crsf, self._router = mavlink, msp, crsf, router
        self._may_probe = may_probe
        self._run_async = run_async
        self._clock = clock
        self._store = self._load()
        self._active = False
        self._state = "idle"  # idle, searching, none, streaming, waiting
        self._generation = 0
        self._channel = None
        self._shell = None
        self._searched_at = {}
        self._udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._detected.connect(self._apply_detected)
        self._data.connect(self._route)
        self._ended.connect(self._stream_ended)
        self._retry = QTimer(self)
        self._retry.setSingleShot(True)
        self._retry.setInterval(3000)
        self._retry.timeout.connect(self._start)
        self._poll = QTimer(self)
        self._poll.setInterval(250)
        self._poll.timeout.connect(self._ask_msp)
        self._poll_index = 0

    # --- saved per camera: what was found, and what the pilot set by hand ------------------
    def _load(self) -> dict:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self):
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(self._store, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def _device(self):
        return getattr(self._devices, "activeId", "") or ""

    def _entry(self) -> dict:
        return dict(self._store.get(self._device(), {}))

    def _link(self) -> dict:
        """The port, speed and protocol to use: by hand where set, else what was found."""
        entry = self._entry()
        found = entry.get("found") or {}
        manual = entry.get("manual") or {}
        link = {k: manual.get(k) or found.get(k) for k in ("port", "baud", "protocol")}
        link["detail"] = found.get("detail", "") if not manual.get("protocol") else ""
        try:
            check_port(link["port"])
            check_baud(link["baud"])
        except (TypeError, ValueError):
            return {}
        return link if link.get("protocol") in PROTOCOLS else {}

    # --- what QML shows ---------------------------------------------------------------------
    @Property(str, notify=changed)
    def text(self):
        link = self._link()
        if self._state == "searching":
            return "шукаю польотник на портах камери…"
        if self._state == "streaming" and link:
            return "дані надходять · " + link_text(link)
        if self._state == "waiting" and link:
            return "чекаю дані · " + link_text(link)
        if link:
            return link_text(link)
        if self._state == "none":
            return "польотник на портах камери не знайдено"
        return "ще не шукали"

    @Property(bool, notify=changed)
    def streaming(self):
        return self._state == "streaming"

    @Property("QVariantMap", notify=changed)
    def manual(self):
        return dict(self._entry().get("manual") or {})

    @Property("QVariantList", constant=True)
    def bauds(self):
        return list(BAUDS)

    @Property("QVariantList", notify=changed)
    def ports(self):
        return list(self._entry().get("ports") or [])

    # --- control -------------------------------------------------------------------------------
    @Slot(bool)
    def setActive(self, active):
        self._active = bool(active)
        if self._active:
            self._start()
        else:
            self._stop()
            self._state = "idle" if not self._link() else self._state
            self.changed.emit()

    @Slot(str, int, str)
    def setManual(self, port, baud, protocol):
        """By hand: an empty port / 0 speed / empty protocol means "auto"."""
        manual = {}
        if port:
            manual["port"] = check_port(port)
        if baud:
            manual["baud"] = check_baud(baud)
        if protocol:
            if protocol not in PROTOCOLS:
                raise ValueError("protocol")
            manual["protocol"] = protocol
        entry = self._entry()
        entry["manual"] = manual
        self._store[self._device()] = entry
        self._save()
        self._restart()

    @Slot()
    def search(self):
        """Look for the flight controller again (the pilot asked)."""
        entry = self._entry()
        entry.pop("found", None)
        self._store[self._device()] = entry
        self._searched_at.pop(self._device(), None)
        self._save()
        self._restart()

    def _restart(self):
        self._stop()
        self.changed.emit()
        if self._active:
            self._start()

    def _host(self):
        device = self._device()
        return self._connections.control_host(device) if device else ""

    def _run(self, work):
        if self._run_async:
            threading.Thread(target=work, name="fc-link", daemon=True).start()
        else:
            work()

    def _start(self):
        if not self._active or self._channel is not None or self._state == "searching":
            return
        host = self._host()
        if not host:
            self._retry.start()
            return
        link = self._link()
        manual = self._entry().get("manual") or {}
        if not link or (manual and not all(k in manual for k in ("port", "baud", "protocol"))):
            device = self._device()
            # Searching listens on every port: never while armed, and not more than once a minute.
            if self._may_probe() and self._clock() - self._searched_at.get(device, -1e9) > 60:
                self._search(device, host, manual)
            return
        self._open_stream(host, link)

    def _search(self, device, host, manual):
        self._state = "searching"
        self._searched_at[device] = self._clock()
        self.changed.emit()

        def work():
            result = None
            try:
                with self._shell_for(host) as session:
                    _code, text = session.run(LIST_COMMAND)
                    ports = parse_ports(text)
                    try_ports = [manual["port"]] if manual.get("port") else ports
                    bauds = (manual["baud"],) if manual.get("baud") else BAUDS
                    found = detect(session, try_ports, bauds, manual.get("protocol", ""))
                    result = {"ports": ports, "found": found}
            except Exception:
                result = None
            self._detected.emit(device, result)

        self._run(work)

    def _apply_detected(self, device, result):
        entry = dict(self._store.get(device, {}))
        if result is not None:
            entry["ports"] = result["ports"]
            if result["found"]:
                entry["found"] = result["found"]
        self._store[device] = entry
        self._save()
        self._state = "idle" if (result and result["found"]) else "none"
        self.changed.emit()
        if self._active and device == self._device() and self._link():
            self._start()
        elif self._active:
            self._retry.start()

    # --- bringing the data -------------------------------------------------------------------------
    def _open_stream(self, host, link):
        self._generation += 1
        generation = self._generation
        self._state = "waiting"
        if self._router is not None:
            self._router.select(link["protocol"])
        if link["protocol"] == "MAVLink":
            self._ensure_mavlink_listens()
        self.changed.emit()
        command = stream_command(link["port"], link["baud"])

        def work():
            try:
                shell = self._shell_for(host)
                session = shell.__enter__()
                channel = session.client.get_transport().open_session()
                channel.exec_command(command)
                self._shell, self._channel = shell, channel
                while generation == self._generation:
                    data = channel.recv(4096)
                    if not data:
                        break
                    self._data.emit(generation, bytes(data))
            except Exception:
                pass
            self._ended.emit(generation)

        self._run(work)
        if link["protocol"] == "MSP":
            self._poll.start()

    def _ensure_mavlink_listens(self):
        """The station's MAVLink reader must listen where the bridge sends (UDP 14550 on this PC)."""
        m = self._mavlink
        if m is None:
            return
        endpoint = str(getattr(m, "endpoint", ""))
        listens = endpoint.startswith("udpin:") and endpoint.endswith(f":{MAVLINK_LOCAL_PORT}")
        connected = (getattr(m, "telemetry", {}) or {}).get("connected") is True
        if not connected and (not listens or not getattr(m, "enabled", True)):
            m.configure(f"udpin:127.0.0.1:{MAVLINK_LOCAL_PORT}", 57600, True)

    def _route(self, generation, data):
        if generation != self._generation:
            return
        protocol = (self._link() or {}).get("protocol")
        if self._state != "streaming":
            self._state = "streaming"
            self.changed.emit()
        if protocol == "MAVLink":
            try:
                self._udp.sendto(data, ("127.0.0.1", MAVLINK_LOCAL_PORT))
            except OSError:
                pass
        elif protocol == "MSP" and self._msp is not None:
            self._msp.feed(data)
        elif protocol == "CRSF" and self._crsf is not None:
            self._crsf.feed(data)

    def _ask_msp(self):
        commands = (1, 2, 3, 101, 106, 108, 109, 110)
        command = commands[self._poll_index % len(commands)]
        self._poll_index += 1
        channel = self._channel
        if channel is not None:
            try:
                channel.sendall(build_request(command))
            except Exception:
                pass

    def _stream_ended(self, generation):
        if generation != self._generation:
            return
        self._close()
        self._state = "waiting" if self._link() else "idle"
        self.changed.emit()
        if self._active:
            self._retry.start()

    def _close(self):
        self._poll.stop()
        channel, shell = self._channel, self._shell
        self._channel = self._shell = None
        for closer in (lambda: channel and channel.close(), lambda: shell and shell.__exit__(None, None, None)):
            try:
                closer()
            except Exception:
                pass

    def _stop(self):
        self._generation += 1
        self._retry.stop()
        self._close()
        if self._state in ("streaming", "waiting"):
            self._state = "idle"
