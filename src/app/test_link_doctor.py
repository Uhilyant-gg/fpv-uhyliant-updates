import pytest
from PySide6.QtCore import QObject, Signal

from link_doctor import LinkDoctor, diagnose, internet_reachable


@pytest.mark.parametrize(
    ("kind", "stream", "internet", "reachable", "code", "text"),
    [
        ("starlink", None, False, None, "pc-offline", "Пропав інтернет на ПК пілота"),
        (
            "static",
            {"packets": 40},
            True,
            None,
            "no-picture",
            "Відео приходить, але не показується · чекаю повного кадру",
        ),
        ("starlink", None, True, True, "camera-silent", "Камера на зв’язку, але не надсилає відео"),
        (
            "starlink",
            None,
            True,
            False,
            "camera-unreachable",
            "Камера не відповідає · ймовірно, зник зв’язок Starlink на дроні",
        ),
        ("cloud", None, True, False, "camera-unreachable", "Камера не відповідає через ZeroTier"),
        ("local", None, False, False, "camera-unreachable", "Камера не відповідає в локальній мережі"),
        ("static", {"packets": 0}, True, None, "no-packets", "Від камери не надходить жодного пакета відео"),
        ("starlink", None, None, None, "checking", "Визначаю причину…"),
    ],
)
def test_the_first_broken_link_is_named(kind, stream, internet, reachable, code, text):
    verdict = diagnose(kind, True, stream, internet, reachable)
    assert (verdict["code"], verdict["level"], verdict["text"]) == (code, "lost", text)


def test_local_flight_does_not_blame_the_internet():
    assert diagnose("local", True, None, False, True)["code"] == "camera-silent"


def test_warnings_while_the_video_plays():
    assert (
        diagnose("static", False, {"lossPct": 8.5, "jitterMs": 2})["text"]
        == "Втрачається 8,5% пакетів · канал перевантажений"
    )
    assert diagnose("static", False, {"lossPct": 0, "jitterMs": 45})["code"] == "jitter"
    ok = diagnose("static", False, {"lossPct": 1.0, "jitterMs": 5})
    assert ok == {"code": "ok", "level": "ok", "text": ""}
    assert diagnose("starlink", False, None, False)["code"] == "ok", "video plays: nothing to blame"


def test_internet_check_tries_the_next_host():
    tried = []

    class Conn:
        def close(self):
            pass

    def connect(address, timeout):
        tried.append(address[0])
        if address[0] != "8.8.8.8":
            raise OSError
        return Conn()

    assert internet_reachable(connect=connect) is True and tried == ["1.1.1.1", "8.8.8.8"]
    assert internet_reachable(connect=lambda a, timeout: (_ for _ in ()).throw(OSError())) is False


class Monitor:
    lost = False


class Devices:
    activeId = "c1"


class Connections(QObject):
    changed = Signal()

    def __init__(self, kind):
        super().__init__()
        self.selected = {"c1": kind}
        self.statuses = {"c1": {kind: {"state": "available"}}}
        self.windows = []
        self.probes = []

    def relay_window(self, device_id):
        return self.windows.pop(0) if self.windows else None

    def probeSelected(self, device_id):
        self.probes.append(device_id)


class Clock:
    def __init__(self):
        self.now = 50.0

    def __call__(self):
        return self.now


def make(kind, internet=True):
    monitor, connections, clock = Monitor(), Connections(kind), Clock()
    checks = []

    def check():
        checks.append(clock.now)
        return internet

    doctor = LinkDoctor(monitor, Devices(), connections, internet_check=check, run_async=False, clock=clock)
    return doctor, monitor, connections, clock, checks


def test_doctor_names_the_cause_when_the_link_is_lost():
    doctor, monitor, connections, clock, checks = make("starlink")
    doctor.evaluate()
    assert doctor.code == "ok" and checks == [], "nothing is checked off the flight screen"
    doctor.setActive(True)
    doctor.evaluate()
    assert doctor.code == "ok" and checks == [50.0]
    monitor.lost = True
    connections.statuses["c1"]["starlink"]["state"] = "unavailable"
    clock.now += 1
    doctor.evaluate()
    assert doctor.text == "Камера не відповідає · ймовірно, зник зв’язок Starlink на дроні"
    assert connections.probes == ["c1"], "the camera is pinged at once when the video is lost"
    clock.now += 1
    doctor.evaluate()
    assert connections.probes == ["c1"]
    clock.now += 1.5
    doctor.evaluate()
    assert connections.probes == ["c1", "c1"] and checks == [50.0, 53.5]


def test_doctor_blames_the_pc_when_its_internet_is_gone():
    doctor, monitor, connections, clock, checks = make("static", internet=False)
    doctor.setActive(True)
    monitor.lost = True
    doctor.evaluate()
    assert doctor.code == "pc-offline" and doctor.level == "lost"
    assert doctor.details["internet"] is False


def test_a_restarted_camera_stream_is_reopened_at_once():
    doctor, monitor, connections, clock, checks = make("static")
    retries = []
    doctor.retryNeeded.connect(lambda: retries.append(1))
    doctor.setActive(True)
    connections.windows = [{"packets": 30, "lossPct": 0.0, "jitterMs": 1, "kbps": 3000, "restarted": True}]
    doctor.evaluate()
    assert retries == [1]
    assert doctor.details["kbps"] == 3000 and doctor.details["hasStream"] is True


def test_local_flight_skips_the_internet_check():
    doctor, monitor, connections, clock, checks = make("local")
    doctor.setActive(True)
    doctor.evaluate()
    assert checks == []


def test_static_ip_is_judged_by_packets_not_by_an_old_status():
    doctor, monitor, connections, clock, checks = make("static")
    doctor.setActive(True)
    monitor.lost = True
    connections.windows = [{"packets": 0, "lossPct": 0.0, "jitterMs": 0, "kbps": 0, "restarted": False}]
    doctor.evaluate()
    assert doctor.text == "Від камери не надходить жодного пакета відео"
    assert connections.probes == [], "nothing to ping with a static IP"
