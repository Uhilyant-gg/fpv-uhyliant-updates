"""Connection choice per camera, with live reachability of every connection type.

Each type is probed in the background (a TCP connect to the camera's video port)
so the home screen shows current status without blocking the UI. "Fly" becomes
possible only after the pilot picks a type that is reachable right now, and the
video then uses that type's address.
"""

from __future__ import annotations

import socket
import threading
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

import connection_profiles as cp
import push_video as pv
import zerotier_local as zt

PUSH_FRESH_S = 3.0
SETUP_RETRY_S = 60.0
SETUP_LABELS = {
    "no-access": "потрібен пароль камери",
    "unsafe": "ключ камери змінився",
    "failed": "камера не налаштувалась",
}
BIND_LABELS = {"grey": "сіра адреса", "no-internet": "немає інтернету"}

PROBE_INTERVAL_MS = 5000
PROBE_TIMEOUT_S = 1.5


def tcp_probe(host: str, port: int, timeout: float = PROBE_TIMEOUT_S) -> int | None:
    """Return the TCP connect time in ms, or None when the camera does not answer."""
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError:
        return None
    return max(1, round((time.monotonic() - started) * 1000))


class ConnectionsRuntime(QObject):
    changed = Signal()
    _probed = Signal(str, str, str, object)  # device id, type, host, latency ms or None
    _ztSnapshot = Signal(object)
    _bound = Signal(str, object)
    _setupDone = Signal(str, object)

    def __init__(
        self,
        devices,
        store,
        prober=tcp_probe,
        interval_ms=PROBE_INTERVAL_MS,
        run_async=True,
        zerotier=None,
        listen=True,
        sdp_folder=None,
        binder=None,
        clock=time.monotonic,
        camera_setup=None,
    ):
        super().__init__()
        self._camera_setup = camera_setup
        self._setup: dict[str, dict] = {}
        self._setup_busy: set[str] = set()
        self._setupDone.connect(self._apply_setup)
        self._listen = listen
        self._listening_paused = False
        self._sockets: dict[int, object] = {}
        self._push_seen: dict[int, float] = {}
        self._clock = clock
        self._sdp_folder = sdp_folder
        self._binder = binder
        self._bind_status: dict = {}
        self._bound.connect(self._apply_bind)
        self._zerotier = zerotier
        self._zt = {"service": "missing", "nodeId": "", "networks": {}, "peers": {}}
        self._zt_busy = False
        self._ztSnapshot.connect(self._apply_zerotier)
        self._devices = devices
        self._store = store
        self._prober = prober
        self._run_async = run_async
        self._addresses = store.load()
        self._selected: dict[str, str] = {}
        self._statuses: dict[str, dict[str, dict]] = {}
        self._in_flight: set[tuple[str, str]] = set()
        self._probed.connect(self._apply_probe)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.refresh)
        for name in ("changed", "streamsChanged"):
            signal = getattr(devices, name, None)
            if signal is not None:
                signal.connect(self._devices_changed)
        self._rebuild()

    # --- properties used by QML ------------------------------------------------
    @Property("QVariantMap", notify=changed)
    def statuses(self):
        return self._statuses

    @Property("QVariantMap", notify=changed)
    def selected(self):
        return dict(self._selected)

    @Property(str, notify=changed)
    def zerotierState(self):
        return self._zt.get("service", "missing") if self._zerotier is not None else "missing"

    @Property(str, notify=changed)
    def zerotierText(self):
        return zt.SERVICE_TEXT.get(self.zerotierState, "")

    @Property(str, notify=changed)
    def zerotierNodeId(self):
        return self._zt.get("nodeId", "")

    @Property("QVariantMap", notify=changed)
    def cameraSetup(self):
        return {k: dict(v) for k, v in self._setup.items()}

    @Slot(str)
    def retryCameraSetup(self, device_id):
        self._setup.pop(device_id, None)
        self._auto_setup(device_id)

    @Property("QVariantMap", notify=changed)
    def bindStatus(self):
        return dict(self._bind_status)

    @Property("QVariantList", constant=True)
    def types(self):
        return [
            {"key": kind, "label": cp.LABELS[kind], "needsAddress": kind in cp.ADDRESS_TYPES or kind == "cloud"}
            for kind in cp.TYPES
        ]

    # --- slots -----------------------------------------------------------------
    @Slot()
    def start(self):
        self.refresh()
        self._timer.start()

    @Slot()
    def stop(self):
        self._timer.stop()
        self._close_listeners()

    @Slot()
    def pauseListening(self):
        """Free the video ports for the player while flying."""
        self._listening_paused = True
        self._close_listeners()

    @Slot()
    def resumeListening(self):
        self._listening_paused = False
        self._sync_listeners()

    @Slot(str, result=int)
    def pushPortFor(self, device_id):
        return int(self._addresses.get(device_id, {}).get("pushPort", 0))

    @Slot(str)
    def bindThisNetwork(self, device_id):
        """Find this network's public address, check it and open the camera's port on the router."""
        if device_id not in self._statuses or self._bind_status.get("busy"):
            return
        port = self._ensure_push_port(device_id)
        self._bind_status = {"deviceId": device_id, "busy": True, "state": "", "message": "Перевіряю мережу…"}
        self._update_push_statuses()
        binder = self._binder or (lambda p: pv.bind_this_network(p, pv.Upnp(), pv.public_ip_https, pv.lan_address))

        def work():
            try:
                result = binder(port)
            except Exception:
                result = {"state": "no-internet", "message": "Не вдалося перевірити мережу."}
            self._bound.emit(device_id, result)

        if self._run_async:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()

    @Slot(str, str, result=bool)
    def select(self, device_id, kind):
        if kind not in cp.TYPES or device_id not in self._statuses:
            return False
        self._selected[device_id] = kind
        self.changed.emit()
        if kind == "cloud":
            self._join_camera_network(device_id)
            self.refresh()
        elif kind == "static":
            self._update_push_statuses()
        else:
            self._probe(device_id, kind)
        return True

    @Slot(str, str, result=str)
    def addressFor(self, device_id, kind):
        return self._addresses.get(device_id, {}).get(kind, "")

    @Slot(str, str, str, result=bool)
    def setAddress(self, device_id, kind, address):
        if kind not in cp.ADDRESS_TYPES:
            return False
        try:
            value = cp.validate_address(kind, address)
        except ValueError:
            return False
        self._addresses.setdefault(device_id, {})[kind] = value
        if kind == "static":
            self._ensure_push_port(device_id)
        self._store.save(self._addresses)
        self._rebuild()
        if kind != "static":
            self._probe(device_id, kind)
        else:
            self._auto_setup(device_id)
        return True

    @Slot(str, result=str)
    def zerotierNetworkFor(self, device_id):
        return self._addresses.get(device_id, {}).get("ztNetwork", "")

    @Slot(str, result=str)
    def zerotierNodeFor(self, device_id):
        return self._addresses.get(device_id, {}).get("ztNode", "")

    @Slot(str, str, str, result=bool)
    def setZeroTier(self, device_id, network_id, node_id):
        """Camera's ZeroTier network and node IDs; both empty removes them."""
        addresses = self._addresses.setdefault(device_id, {})
        if not str(network_id).strip() and not str(node_id).strip():
            addresses.pop("ztNetwork", None)
            addresses.pop("ztNode", None)
        else:
            try:
                network, node = zt.validate_network_id(network_id), zt.validate_node_id(node_id)
            except ValueError:
                return False
            addresses.update(ztNetwork=network, ztNode=node)
        if not addresses:
            self._addresses.pop(device_id, None)
        self._store.save(self._addresses)
        if self._selected.get(device_id) == "cloud" and "ztNetwork" not in addresses:
            self._selected.pop(device_id)
        self._rebuild()
        self.refresh()
        return True

    @Slot(str, str)
    def clearAddress(self, device_id, kind):
        addresses = self._addresses.get(device_id, {})
        if kind in addresses:
            del addresses[kind]
            if not addresses:
                self._addresses.pop(device_id, None)
            self._store.save(self._addresses)
            if self._selected.get(device_id) == kind:
                self._selected.pop(device_id)
            self._rebuild()

    @Slot(str, result=bool)
    def canFly(self, device_id):
        return cp.can_fly(self._selected.get(device_id, ""), self._statuses.get(device_id, {}))

    @Slot()
    def refresh(self):
        for device_id, statuses in self._statuses.items():
            for kind, entry in statuses.items():
                if kind not in ("cloud", "static") and entry["state"] not in ("unconfigured", "unsupported"):
                    self._probe(device_id, kind)
        self._update_push_statuses()
        for device_id in list(self._statuses):
            self._auto_setup(device_id)
        self._refresh_zerotier()

    # --- used by the video runtime ---------------------------------------------
    def host_for(self, device) -> str:
        """Address the video should use for this camera, by the selected connection type."""
        device_id = device.get("id", "")
        kind = self._selected.get(device_id, "local")
        if kind in ("starlink", "cloud"):
            return self._host(device_id, kind)
        return str(device.get("host", "")).strip()

    def push_url_for(self, device) -> str:
        """For "Static IP" the camera sends RTP here; the player opens it through an SDP file."""
        device_id = device.get("id", "")
        port = self.pushPortFor(device_id)
        if self._selected.get(device_id) != "static" or not port or self._sdp_folder is None:
            return ""
        addresses = self._addresses[device_id]
        path = pv.write_sdp(
            self._sdp_folder, device_id, port, addresses.get("pushCodec", "h265"), addresses.get("pushPayload")
        )
        return path.as_uri()

    # --- internals -------------------------------------------------------------
    def _devices_changed(self):
        self._rebuild()

    def _port(self, device_id):
        for stream in getattr(self._devices, "streams", []):
            if stream.get("device_id") == device_id and stream.get("enabled"):
                try:
                    return int(stream.get("port"))
                except (TypeError, ValueError):
                    break
        return cp.DEFAULT_VIDEO_PORT

    def _host(self, device_id, kind):
        if kind == "local":
            device = next((d for d in self._devices.items if d.get("id") == device_id), {})
            return str(device.get("host", "")).strip()
        if kind in cp.ADDRESS_TYPES:
            return self._addresses.get(device_id, {}).get(kind, "")
        if kind == "cloud":
            addresses = self._addresses.get(device_id, {})
            if addresses.get("ztNetwork") and addresses.get("ztNode"):
                return zt.rfc4193_address(addresses["ztNetwork"], addresses["ztNode"])
        return ""

    def _rebuild(self):
        statuses = {}
        for device in self._devices.homeItems:
            device_id = device.get("id", "")
            old = self._statuses.get(device_id, {})
            entry = {}
            for kind in cp.TYPES:
                if kind == "cloud" and self._zerotier is None:
                    entry[kind] = cp.status_entry("unsupported")
                elif not self._host(device_id, kind):
                    entry[kind] = cp.status_entry("unconfigured", None, "вказати мережу" if kind == "cloud" else None)
                elif kind == "static":
                    entry[kind] = (
                        old.get(kind)
                        if old.get(kind, {}).get("state") in ("available", "unavailable")
                        else cp.status_entry("unavailable", None, "чекає камеру")
                    )
                elif kind in old and old[kind]["state"] not in ("unconfigured", "unsupported"):
                    entry[kind] = old[kind]
                else:
                    entry[kind] = cp.status_entry("checking")
            statuses[device_id] = entry
        self._statuses = statuses
        self._selected = {k: v for k, v in self._selected.items() if k in statuses}
        self._update_push_statuses(emit=False)
        self._sync_listeners()
        self.changed.emit()

    # --- video pushed by the camera to this PC ("Static IP") ------------------------
    def _ensure_push_port(self, device_id):
        addresses = self._addresses.setdefault(device_id, {})
        if not addresses.get("pushPort"):
            used = {a.get("pushPort") for a in self._addresses.values() if a.get("pushPort")}
            addresses["pushPort"] = pv.free_port(used)
            self._store.save(self._addresses)
        return addresses["pushPort"]

    def _note_packet(self, port, when=None, payload=None):
        first = self._clock() - self._push_seen.get(port, -1e9) > PUSH_FRESH_S
        self._push_seen[port] = self._clock() if when is None else when
        if payload is not None:
            # The video's RTP payload type is learnt from the packets themselves.
            for addresses in self._addresses.values():
                if addresses.get("pushPort") == port and addresses.get("pushPayload") != payload:
                    addresses["pushPayload"] = payload
                    self._store.save(self._addresses)
        if first:
            self._update_push_statuses()

    def _update_push_statuses(self, emit=True):
        now = self._clock()
        for device_id, statuses in self._statuses.items():
            if "static" not in statuses:
                continue
            if statuses["static"]["state"] == "unconfigured":
                bind = self._bind_status if self._bind_status.get("deviceId") == device_id else {}
                label = "визначаю адресу…" if bind.get("busy") else BIND_LABELS.get(bind.get("state"))
                statuses["static"] = cp.status_entry("unconfigured", None, label)
                continue
            port = self.pushPortFor(device_id)
            fresh = port and now - self._push_seen.get(port, -1e9) <= PUSH_FRESH_S
            setup = self._setup.get(device_id, {}).get("state")
            bind = self._bind_status.get("state") if self._bind_status.get("deviceId") == device_id else None
            waiting = SETUP_LABELS.get(setup) or BIND_LABELS.get(bind) or "чекає камеру"
            statuses["static"] = (
                cp.status_entry("available", None, "камера надсилає")
                if fresh
                else cp.status_entry("unavailable", None, waiting)
            )
        if emit:
            self.changed.emit()

    def _sync_listeners(self):
        if not self._listen or self._listening_paused:
            return
        wanted = {self.pushPortFor(d) for d in self._statuses if self.pushPortFor(d)}
        for port in list(self._sockets):
            if port not in wanted:
                self._sockets.pop(port).close()
        for port in wanted - set(self._sockets):
            from PySide6.QtNetwork import QHostAddress, QUdpSocket

            sock = QUdpSocket(self)
            if sock.bind(QHostAddress(QHostAddress.AnyIPv4), port):
                sock.readyRead.connect(lambda port=port, sock=sock: self._drain(port, sock))
                self._sockets[port] = sock
            else:
                sock.deleteLater()

    def _drain(self, port, sock):
        payload = None
        while sock.hasPendingDatagrams():
            packet = bytes(sock.receiveDatagram(2048).data())
            payload = pv.rtp_payload_type(packet) or payload
        self._note_packet(port, payload=payload)

    def _close_listeners(self):
        for sock in self._sockets.values():
            sock.close()
        self._sockets.clear()

    def _apply_bind(self, device_id, result):
        self._bind_status = {"deviceId": device_id, "busy": False, **result}
        if result.get("state") in ("ready", "manual") and result.get("publicIp"):
            self.setAddress(device_id, "static", result["publicIp"])
        self._update_push_statuses()

    # --- configure the camera itself (over SSH, on the local network) -------------
    def _auto_setup(self, device_id):
        """Point the camera at the pilot's static IP as soon as that is possible and safe."""
        addresses = self._addresses.get(device_id, {})
        address, port = addresses.get("static"), addresses.get("pushPort")
        if self._camera_setup is None or not address or not port or self._listening_paused:
            return
        if (
            device_id in self._setup_busy
            or self._statuses.get(device_id, {}).get("local", {}).get("state") != "available"
        ):
            return
        target = f"udp://{address}:{port}"
        if addresses.get("pushConfigured") == target:
            return
        last = self._setup.get(device_id, {})
        if last.get("target") == target and self._clock() - last.get("at", -1e9) < SETUP_RETRY_S:
            return
        host = self._host(device_id, "local")
        self._setup_busy.add(device_id)
        self._setup[device_id] = {
            "state": "working",
            "message": "Налаштовую камеру…",
            "target": target,
            "at": self._clock(),
        }
        self.changed.emit()

        def work():
            try:
                result = self._camera_setup(host, address, port)
            except Exception:
                result = {"state": "failed", "message": ""}
            self._setupDone.emit(device_id, dict(result, target=target))

        if self._run_async:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()

    def _apply_setup(self, device_id, result):
        self._setup_busy.discard(device_id)
        self._setup[device_id] = dict(result, at=self._clock())
        addresses = self._addresses.setdefault(device_id, {})
        if result.get("state") in ("configured", "already"):
            addresses["pushConfigured"] = result["target"]
            if result.get("codec") in ("h264", "h265"):
                addresses["pushCodec"] = result["codec"]
            self._store.save(self._addresses)
        self._update_push_statuses()

    def _probe(self, device_id, kind):
        host = self._host(device_id, kind)
        if not host or (device_id, kind) in self._in_flight:
            return
        port = self._port(device_id)
        self._in_flight.add((device_id, kind))

        def work():
            try:
                latency = self._prober(host, port)
            except Exception:
                latency = None
            self._probed.emit(device_id, kind, host, latency)

        if self._run_async:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()

    def _apply_probe(self, device_id, kind, host, latency):
        self._in_flight.discard((device_id, kind))
        if device_id not in self._statuses or self._host(device_id, kind) != host:
            return  # the camera or its address changed while probing
        state = "available" if latency is not None else "unavailable"
        label = None
        if kind == "cloud" and latency is not None:
            label = zt.path_label(self._zt, self._addresses[device_id]["ztNode"], latency)
        self._statuses[device_id][kind] = cp.status_entry(state, latency, label)
        self.changed.emit()

    # --- ZeroTier ----------------------------------------------------------------
    def _refresh_zerotier(self):
        if self._zerotier is None or self._zt_busy:
            return
        self._zt_busy = True

        def work():
            try:
                snapshot = self._zerotier.snapshot()
            except Exception:
                snapshot = {"service": "stopped", "nodeId": "", "networks": {}, "peers": {}}
            self._ztSnapshot.emit(snapshot)

        if self._run_async:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()

    def _apply_zerotier(self, snapshot):
        self._zt_busy = False
        self._zt = snapshot
        for device_id, statuses in self._statuses.items():
            addresses = self._addresses.get(device_id, {})
            if "cloud" not in statuses or not addresses.get("ztNetwork"):
                continue
            state, label = zt.cloud_status(snapshot, addresses["ztNetwork"], addresses["ztNode"])
            if state == "ready":
                self._probe(device_id, "cloud")
            else:
                statuses["cloud"] = cp.status_entry("unavailable", None, label)
        self.changed.emit()

    def _join_camera_network(self, device_id):
        network = self._addresses.get(device_id, {}).get("ztNetwork")
        if self._zerotier is None or not network or network in self._zt.get("networks", {}):
            return
        if self._run_async:
            threading.Thread(target=self._zerotier.join, args=(network,), daemon=True).start()
        else:
            self._zerotier.join(network)
