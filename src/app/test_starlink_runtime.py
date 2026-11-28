import starlink_dish as sd
from starlink_runtime import StarlinkRuntime
from test_starlink_dish import msg, packed_bools, packed_floats, status_message, vint


class Devices:
    activeId = "c1"


class Connections:
    def __init__(self, host="10.147.17.5"):
        self.host = host

    def control_host(self, device_id):
        return self.host


class Shell:
    opened = 0
    closed = 0
    answers = {}
    fail = False

    def __init__(self, host):
        self.host = host

    def __enter__(self):
        Shell.opened += 1
        return self

    def __exit__(self, *exc):
        Shell.closed += 1
        return False

    def open_tcp(self, host, port):
        assert (host, port) == ("192.168.100.1", 9201)
        if Shell.fail:
            raise OSError("no route")
        return Channel(Shell.answers)


class Channel:
    def __init__(self, answers):
        self.answers = answers
        self.sent = b""
        self.reply = None

    def settimeout(self, t):
        pass

    def sendall(self, data):
        self.sent += data
        field = sd.GET_HISTORY if data.endswith(sd.frame(sd.request(sd.GET_HISTORY))) else sd.GET_STATUS
        body = sd.frame(self.answers[field])
        self.reply = [b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n" % len(body) + body, b""]

    def recv(self, n):
        return self.reply.pop(0)

    def close(self):
        pass


def make(host="10.147.17.5"):
    Shell.opened = Shell.closed = 0
    Shell.fail = False
    size, current = 10, 25
    obstructed = [False] * size
    for second in (22, 23):
        obstructed[second % size] = True
    history = (
        vint(1, current)
        + packed_floats(1001, [0.0] * size)
        + packed_bools(1006, [True] * size)
        + packed_bools(1007, obstructed)
    )
    Shell.answers = {
        sd.GET_STATUS: msg(sd.DISH_GET_STATUS, status_message()),
        sd.GET_HISTORY: msg(sd.DISH_GET_HISTORY, history),
    }
    return StarlinkRuntime(Devices(), Connections(host), Shell, run_async=False)


def test_status_in_flight_through_one_kept_session():
    rt = make()
    rt.setActive(True)
    rt.poll()
    assert rt.available and rt.status["latencyMs"] == 42 and rt.status["obstructedPct"] == 3.1
    assert Shell.opened == 1, "one login, the session is kept between reads"
    assert rt.warning() == "Starlink: перешкода в небі зараз"
    rt.setActive(False)
    assert Shell.closed == 1


def test_cause_of_the_last_dropout_from_the_dish_history():
    rt = make()
    rt.explainOutage(3)
    assert rt.lastOutageCause.startswith("перешкода в небі")


def test_no_camera_path_or_a_silent_dish_is_explained():
    rt = make(host="")
    rt.poll()
    assert not rt.available and rt.reason.startswith("Антену видно лише через ZeroTier")
    rt = make()
    Shell.fail = True
    rt.poll()
    assert not rt.available and rt.reason == "Антена Starlink не відповідає через камеру"
    assert Shell.closed == 1, "a failed session is closed and reopened next time"
