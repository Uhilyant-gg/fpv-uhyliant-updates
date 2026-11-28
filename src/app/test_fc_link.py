import socket

from PySide6.QtCore import QCoreApplication

import fc_link as fl
from msp_runtime import MspRuntime

APP = QCoreApplication.instance() or QCoreApplication([])


def mavlink_bytes(n=3):
    from pymavlink.dialects.v20 import ardupilotmega as mavlink

    m = mavlink.MAVLink(None, srcSystem=1, srcComponent=1)
    out = b""
    for _ in range(n):
        out += m.heartbeat_encode(mavlink.MAV_TYPE_QUADROTOR, mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA, 0, 0, 0).pack(m)
        out += m.attitude_encode(0, 0.1, 0.2, 0.3, 0, 0, 0).pack(m)
    return out


def msp_variant_reply(name=b"BTFL"):
    payload = name
    checksum = len(payload) ^ 2
    for b in payload:
        checksum ^= b
    return b"$M>" + bytes((len(payload), 2)) + payload + bytes((checksum,))


def crsf_frame(frame_type, payload):
    from crsf_runtime import crc8_dvb_s2

    body = bytes((frame_type,)) + payload
    return bytes((0xC8, len(body) + 1)) + body + bytes((crc8_dvb_s2(body),))


def test_ports_skip_the_console_and_bad_names():
    text = "/dev/ttyAMA0\n/dev/ttyAMA1\n/dev/ttyS2\n/dev/tty;rm\n---\nmem=64M console=ttyAMA0,115200 root=/dev/mtd"
    assert fl.parse_ports(text) == ["/dev/ttyAMA1", "/dev/ttyS2"]


def test_protocols_are_named_by_valid_packets_only():
    assert fl.identify(mavlink_bytes()) == {"protocol": "MAVLink", "detail": "ArduPilot"}
    assert fl.identify(b"\x00\xff" + msp_variant_reply()) == {"protocol": "MSP", "detail": "Betaflight"}
    battery = crsf_frame(0x08, b"\x00\x98\x00\x0c\x00\x00\x01\x4b")
    assert fl.identify(battery * 2) == {"protocol": "CRSF", "detail": ""}
    assert fl.identify(bytes(range(256))) is None, "random bytes are nothing"
    assert fl.identify(b"") is None


def test_commands_take_only_checked_ports_and_speeds():
    command = fl.sample_command("/dev/ttyS2", 115200)
    assert "stty -F /dev/ttyS2 115200 raw" in command and fl.STOP_OLD in command
    assert "exec cat /dev/ttyS2" in fl.stream_command("/dev/ttyS2", 57600)
    for port, baud in (("/dev/ttyS2; reboot", 115200), ("/dev/ttyS2", 12345)):
        try:
            fl.sample_command(port, baud)
            raise AssertionError("refused")
        except ValueError:
            pass
    assert fl.parse_hex(" 24 4d 3e\n 04 02") == b"$M>\x04\x02"


class Session:
    """A camera with an ArduPilot on ttyS2 at 57600."""

    def __init__(self):
        self.commands = []

    def run(self, command):
        self.commands.append(command)
        if command == fl.LIST_COMMAND:
            return 0, "/dev/ttyAMA0\n/dev/ttyS2\n---\nconsole=ttyAMA0,115200"
        if "/dev/ttyS2 57600" in command:
            return 0, " ".join(f"{b:02x}" for b in mavlink_bytes())
        return 0, " ".join(f"{b:02x}" for b in bytes(range(40)))


def test_detect_tries_ports_and_speeds_until_one_speaks():
    session = Session()
    found = fl.detect(session)
    assert found == {"port": "/dev/ttyS2", "baud": 57600, "protocol": "MAVLink", "detail": "ArduPilot"}
    assert not any("/dev/ttyAMA0" in c and "stty" in c for c in session.commands), "the console is never touched"
    assert fl.link_text(found) == "MAVLink · порт ttyS2 · 57600 · ArduPilot"


class Channel:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent = []
        self.command = ""

    def exec_command(self, command):
        self.command = command

    def recv(self, n):
        return self.chunks.pop(0) if self.chunks else b""

    def sendall(self, data):
        self.sent.append(data)

    def close(self):
        pass


class Shell:
    def __init__(self, session, channel):
        self.session = session
        self.channel = channel
        transport = type("T", (), {"open_session": lambda _s: channel})()
        session.client = type("C", (), {"get_transport": lambda _s: transport})()

    def __enter__(self):
        return self.session

    def __exit__(self, *exc):
        return False


class Devices:
    activeId = "cam"


class Connections:
    def control_host(self, device_id):
        return "192.168.1.10"


class Router:
    def __init__(self):
        self.selected = []

    def select(self, name):
        self.selected.append(name)
        return True


def test_found_mavlink_is_brought_to_the_station_over_ssh(tmp_path, monkeypatch):
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.bind(("127.0.0.1", 0))
    listener.settimeout(2)
    monkeypatch.setattr(fl, "MAVLINK_LOCAL_PORT", listener.getsockname()[1])
    channel = Channel([mavlink_bytes(1)])
    router = Router()
    armed = [False]
    rt = fl.FcLinkRuntime(
        Devices(),
        Connections(),
        lambda host: Shell(Session(), channel),
        tmp_path / "fc.json",
        router=router,
        may_probe=lambda: not armed[0],
        run_async=False,
    )
    rt.setActive(True)
    assert router.selected == ["MAVLink"]
    assert "exec cat /dev/ttyS2" in channel.command and "57600" in channel.command
    assert listener.recv(4096) == mavlink_bytes(1)
    again = fl.FcLinkRuntime(Devices(), Connections(), lambda h: None, tmp_path / "fc.json")
    assert again.text == "MAVLink · порт ttyS2 · 57600 · ArduPilot", "remembered for this camera"


def test_no_search_while_armed_and_manual_settings(tmp_path):
    calls = []
    armed = [True]

    def shell(host):
        calls.append(host)
        return Shell(Session(), Channel([]))

    rt = fl.FcLinkRuntime(
        Devices(), Connections(), shell, tmp_path / "fc.json", may_probe=lambda: not armed[0], run_async=False
    )
    rt.setActive(True)
    assert calls == [], "listening on the ports only while the drone is not armed"
    rt.setManual("/dev/ttyS2", 57600, "MAVLink")
    assert calls, "set by hand: no search needed, the data is brought at once"
    assert rt.manual == {"port": "/dev/ttyS2", "baud": 57600, "protocol": "MAVLink"}


def test_msp_answers_reach_the_msp_reader_and_questions_are_asked(tmp_path):
    msp = MspRuntime()
    channel = Channel([msp_variant_reply(b"INAV")])
    rt = fl.FcLinkRuntime(
        Devices(), Connections(), lambda h: Shell(Session(), channel), tmp_path / "fc.json", msp=msp, run_async=False
    )
    rt.setManual("/dev/ttyS2", 115200, "MSP")
    rt.setActive(True)
    assert msp.telemetry["link"]["fcVariant"] == "INAV"
