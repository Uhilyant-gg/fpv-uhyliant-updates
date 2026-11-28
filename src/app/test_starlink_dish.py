import struct

import starlink_dish as sd


def varint(value):
    return sd._varint(value)


def field(number, wire, payload):
    return varint(number << 3 | wire) + payload


def f32(number, value):
    return field(number, 5, struct.pack("<f", value))


def vint(number, value):
    return field(number, 0, varint(value))


def msg(number, body):
    return field(number, 2, varint(len(body)) + body)


def packed_floats(number, values):
    body = struct.pack(f"<{len(values)}f", *values)
    return msg(number, body)


def packed_bools(number, values):
    return msg(number, b"".join(varint(int(v)) for v in values))


def status_message():
    obstruction = f32(1, 0.031) + vint(5, 1)
    alerts = vint(3, 1)
    device = vint(1, 7200)
    info = msg(3, b"2026.11.1.mr1")
    return (
        msg(1, info)
        + msg(2, device)
        + vint(1006, 1)
        + f32(1009, 41.6)
        + f32(1003, 0.02)
        + f32(1007, 85.3e6)
        + f32(1008, 12.4e6)
        + msg(1004, obstruction)
        + msg(1005, alerts)
    )


def test_request_bytes_for_get_status():
    assert sd.request(sd.GET_STATUS) == bytes([0xE2, 0x3E, 0x00])


def test_status_for_the_pilot():
    s = sd.status(sd.decode(status_message()))
    assert s == {
        "state": 1,
        "stateText": "на зв’язку",
        "latencyMs": 42,
        "dropPct": 2.0,
        "downMbps": 85.3,
        "upMbps": 12.4,
        "obstructedPct": 3.1,
        "currentlyObstructed": True,
        "alerts": ["антена перегріта, швидкість знижена"],
        "uptimeS": 7200,
        "software": "2026.11.1.mr1",
    }


def test_empty_status_is_unknown_not_an_error():
    s = sd.status({})
    assert s["stateText"] == "стан невідомий" and s["alerts"] == [] and not s["currentlyObstructed"]


def test_grpc_web_round_trip_through_a_channel():
    response = msg(sd.DISH_GET_STATUS, status_message())
    body = sd.frame(response) + b"\x80" + struct.pack(">I", 15) + b"grpc-status:0\r\n"
    chunked = hex(len(body))[2:].encode() + b"\r\n" + body + b"\r\n0\r\n\r\n"
    http = (
        b"HTTP/1.1 200 OK\r\nContent-Type: application/grpc-web+proto\r\nTransfer-Encoding: chunked\r\n\r\n" + chunked
    )

    class Channel:
        def __init__(self):
            self.sent = b""
            self.parts = [http[:50], http[50:], b""]

        def settimeout(self, t):
            pass

        def sendall(self, data):
            self.sent += data

        def recv(self, n):
            return self.parts.pop(0)

        def close(self):
            pass

    channel = Channel()
    opened = []

    def open_channel(host, port):
        opened.append((host, port))
        return channel

    answer = sd.call(open_channel, sd.GET_STATUS, sd.DISH_GET_STATUS)
    assert opened == [("192.168.100.1", 9201)]
    assert channel.sent.startswith(b"POST /SpaceX.API.Device.Device/Handle HTTP/1.1\r\n")
    assert channel.sent.endswith(sd.frame(sd.request(sd.GET_STATUS)))
    assert sd.status(answer)["latencyMs"] == 42


def test_outage_cause_from_the_dish_history():
    size = 10
    current = 23  # ring position: 23 % 10 = 3 is the next slot
    obstructed = [False] * size
    scheduled = [True] * size
    drop = [0.0] * size
    for second in (20, 21):  # two seconds ago
        obstructed[second % size] = True
    hist = sd.history(
        sd.decode(
            vint(1, current)
            + packed_floats(1001, drop)
            + packed_bools(1006, scheduled)
            + packed_bools(1007, obstructed)
        )
    )
    assert sd.last_seconds(hist["obstructed"], current, 3) == [True, True, False]
    assert sd.outage_cause(hist, 4).startswith("перешкода в небі")
    hist["obstructed"] = [False] * size
    hist["scheduled"][2] = False
    assert sd.outage_cause(hist, 4) == "немає супутника в розкладі Starlink"
    hist["scheduled"] = [True] * size
    hist["drop"][1] = 1.0
    assert sd.outage_cause(hist, 4) == "Starlink втратив зв’язок із мережею"
    hist["drop"] = [0.0] * size
    assert sd.outage_cause(hist, 4).startswith("Starlink працював")
