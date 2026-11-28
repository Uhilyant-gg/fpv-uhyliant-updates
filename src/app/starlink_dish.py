"""Read the Starlink dish on the drone: state, latency, loss, obstructions, alerts and
the last minutes of history, to tell the pilot why the link dropped.

The dish answers on its own network (192.168.100.1) next to the camera, so the
station reaches it through the SSH connection to the camera (a forwarded TCP
channel) and speaks gRPC-Web over plain HTTP. No extra libraries: the few
protobuf messages needed are encoded and decoded here. Field numbers follow the
public SpaceX.API.Device protos (device.proto, dish.proto).
"""

from __future__ import annotations

import struct

DISH_HOST = "192.168.100.1"
GRPC_WEB_PORT = 9201
PATH = "/SpaceX.API.Device.Device/Handle"

# Request oneof → Response oneof
GET_STATUS, DISH_GET_STATUS = 1004, 2004
GET_HISTORY, DISH_GET_HISTORY = 1007, 2006

STATE_TEXT = {0: "стан невідомий", 1: "на зв’язку", 2: "шукає супутник", 3: "завантажується"}
ALERT_TEXT = {
    1: "двигуни антени заблоковані",
    2: "антена вимкнулась від перегріву",
    3: "антена перегріта, швидкість знижена",
    4: "антена в незвичному місці",
    5: "антена нахилена",
    6: "повільне підключення кабелю",
}


# --- protobuf wire format (only what the dish needs) ----------------------------
def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def request(field: int) -> bytes:
    """A Request with one empty sub-request (get_status, get_history, …)."""
    return _varint(field << 3 | 2) + _varint(0)


def decode(data: bytes) -> dict[int, list]:
    """Fields of one message: number → list of raw values (int, bytes or float bits)."""
    fields: dict[int, list] = {}
    i = 0
    while i < len(data):
        key, i = _read_varint(data, i)
        number, wire = key >> 3, key & 7
        if wire == 0:
            value, i = _read_varint(data, i)
        elif wire == 1:
            value, i = data[i : i + 8], i + 8
        elif wire == 2:
            length, i = _read_varint(data, i)
            value, i = data[i : i + length], i + length
        elif wire == 5:
            value, i = data[i : i + 4], i + 4
        else:
            raise ValueError("unsupported wire type")
        fields.setdefault(number, []).append(value)
    return fields


def _read_varint(data: bytes, i: int):
    shift = result = 0
    while True:
        if i >= len(data):
            raise ValueError("truncated")
        byte = data[i]
        i += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, i
        shift += 7


def _float(fields, number, default=None):
    raw = fields.get(number)
    if not raw or not isinstance(raw[-1], bytes) or len(raw[-1]) != 4:
        return default
    return struct.unpack("<f", raw[-1])[0]


def _int(fields, number, default=0):
    raw = fields.get(number)
    return raw[-1] if raw and isinstance(raw[-1], int) else default


def _floats(fields, number) -> list[float]:
    """Repeated float: packed (one bytes value) or not."""
    out = []
    for raw in fields.get(number, []):
        if isinstance(raw, bytes):
            out.extend(struct.unpack(f"<{len(raw) // 4}f", raw[: len(raw) // 4 * 4]))
    return out


def _bools(fields, number) -> list[bool]:
    out = []
    for raw in fields.get(number, []):
        if isinstance(raw, int):
            out.append(bool(raw))
        elif isinstance(raw, bytes):
            i = 0
            while i < len(raw):
                value, i = _read_varint(raw, i)
                out.append(bool(value))
    return out


def _message(fields, number) -> dict:
    raw = fields.get(number)
    return decode(raw[-1]) if raw and isinstance(raw[-1], bytes) else {}


# --- gRPC-Web framing ------------------------------------------------------------
def frame(message: bytes) -> bytes:
    return b"\x00" + struct.pack(">I", len(message)) + message


def unframe(body: bytes) -> bytes:
    """The first data frame of a gRPC-Web response body."""
    i = 0
    while i + 5 <= len(body):
        flag, length = body[i], struct.unpack(">I", body[i + 1 : i + 5])[0]
        payload = body[i + 5 : i + 5 + length]
        if not flag & 0x80:
            return payload
        i += 5 + length
    raise ValueError("no data frame")


def http_request(message: bytes) -> bytes:
    body = frame(message)
    head = (
        f"POST {PATH} HTTP/1.1\r\nHost: {DISH_HOST}:{GRPC_WEB_PORT}\r\n"
        "Content-Type: application/grpc-web+proto\r\nX-Grpc-Web: 1\r\nAccept: application/grpc-web+proto\r\n"
        f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
    )
    return head.encode("ascii") + body


def http_body(raw: bytes) -> bytes:
    head, _, body = raw.partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0]
    if b" 200 " not in status + b" ":
        raise ValueError("dish refused")
    if b"transfer-encoding: chunked" in head.lower():
        out, i = bytearray(), 0
        while True:
            end = body.index(b"\r\n", i)
            size = int(body[i:end].split(b";")[0], 16)
            if size == 0:
                return bytes(out)
            out += body[end + 2 : end + 2 + size]
            i = end + 2 + size + 2
    return body


def call(open_channel, field: int, answer: int, timeout=4.0) -> dict:
    """Ask the dish through a channel opened to it; the decoded answer message."""
    channel = open_channel(DISH_HOST, GRPC_WEB_PORT)
    try:
        channel.settimeout(timeout)
        channel.sendall(http_request(request(field)))
        raw = bytearray()
        while True:
            chunk = channel.recv(65536)
            if not chunk:
                break
            raw += chunk
    finally:
        channel.close()
    response = decode(unframe(http_body(bytes(raw))))
    return _message(response, answer)


# --- what the pilot needs --------------------------------------------------------
def status(message: dict) -> dict:
    obstruction = _message(message, 1004)
    alerts = _message(message, 1005)
    device = _message(message, 2)
    info = _message(message, 1)
    return {
        "state": _int(message, 1006, 0),
        "stateText": STATE_TEXT.get(_int(message, 1006, 0), "стан невідомий"),
        "latencyMs": round(_float(message, 1009, 0.0)),
        "dropPct": round(100 * _float(message, 1003, 0.0), 1),
        "downMbps": round(_float(message, 1007, 0.0) / 1e6, 1),
        "upMbps": round(_float(message, 1008, 0.0) / 1e6, 1),
        "obstructedPct": round(100 * _float(obstruction, 1, 0.0), 1),
        "currentlyObstructed": bool(_int(obstruction, 5, 0)),
        "alerts": [ALERT_TEXT[n] for n in sorted(ALERT_TEXT) if _int(alerts, n, 0)],
        "uptimeS": _int(device, 1, 0),
        "software": (info.get(3) or [b""])[-1].decode("utf-8", "replace") if info.get(3) else "",
    }


def history(message: dict) -> dict:
    """The dish keeps per-second rings; ``current`` is the total count written."""
    return {
        "current": _int(message, 1, 0),
        "drop": _floats(message, 1001),
        "obstructed": _bools(message, 1007),
        "scheduled": _bools(message, 1006),
    }


def last_seconds(ring: list, current: int, seconds: int) -> list:
    """The newest ``seconds`` values of a ring buffer, oldest first."""
    size = len(ring)
    if not size:
        return []
    seconds = min(seconds, size, current)
    return [ring[(current - seconds + k) % size] for k in range(seconds)]


def outage_cause(hist: dict, seconds: int) -> str:
    """Why the link dropped during the last ``seconds``, from the dish's own history."""
    seconds = max(1, int(seconds))
    obstructed = last_seconds(hist.get("obstructed", []), hist.get("current", 0), seconds)
    scheduled = last_seconds(hist.get("scheduled", []), hist.get("current", 0), seconds)
    drop = last_seconds(hist.get("drop", []), hist.get("current", 0), seconds)
    if any(obstructed):
        return "перешкода в небі (дерева, будівлі, корпус дрона)"
    if scheduled and not all(scheduled):
        return "немає супутника в розкладі Starlink"
    if drop and max(drop) >= 1.0:
        return "Starlink втратив зв’язок із мережею"
    if drop:
        return "Starlink працював — причина між Starlink і ПК (інтернет, ZeroTier)"
    return ""
