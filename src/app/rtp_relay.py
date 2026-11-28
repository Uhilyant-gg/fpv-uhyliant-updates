"""The station receives the camera's pushed RTP video itself and hands it to the player.

Passing the packets through costs well under a millisecond on the same PC, and in
return the station sees what the player cannot tell: whether packets arrive at all,
how many are lost, how unevenly they come, the real bitrate, and when the camera
restarted its stream (a new source id), so the video can be re-opened at once.
"""

from __future__ import annotations

import socket
import struct
import threading
import time

CLOCK_HZ = 90_000  # RTP video clock


def parse_rtp(data: bytes):
    """(sequence, timestamp, source id, payload type) of an RTP v2 packet, else None."""
    if len(data) < 12 or data[0] >> 6 != 2:
        return None
    _, marker_payload, seq, ts, ssrc = struct.unpack("!BBHII", data[:12])
    return seq, ts, ssrc, marker_payload & 0x7F


CODEC_NAMES = {"h265": "H.265", "h264": "H.264"}


def starts_keyframe(payload: bytes, codec: str) -> bool:
    """Whether this RTP payload begins a full (key) frame: IRAP for H.265, IDR for H.264."""
    if not payload:
        return False
    if codec == "h264":
        nal = payload[0] & 0x1F
        if nal == 28 and len(payload) > 1:  # FU-A: only its first fragment starts the frame
            return bool(payload[1] & 0x80) and (payload[1] & 0x1F) == 5
        return nal == 5
    if len(payload) < 2:
        return False
    nal = (payload[0] >> 1) & 0x3F
    if nal == 49 and len(payload) > 2:  # fragmentation unit
        return bool(payload[2] & 0x80) and 16 <= (payload[2] & 0x3F) <= 21
    return 16 <= nal <= 21


class RtpStats:
    """Counts one window (normally a second) at a time; jitter follows RFC 3550."""

    def __init__(self, codec: str = "h265"):
        self._codec = codec if codec in CODEC_NAMES else "h265"
        self._keyframes: list[float] = []
        self._ssrc = None
        self._max_seq = None
        self._jitter = 0.0
        self._transit = None
        self._last_at = None
        self._reset_window()
        self._restarted = False

    def _reset_window(self):
        self._packets = 0
        self._bytes = 0
        self._expected = 0
        self._restarted = False

    def feed(self, data: bytes, arrival: float):
        header = parse_rtp(data)
        if header is None:
            return
        seq, ts, ssrc, _ = header
        self._last_at = arrival
        if starts_keyframe(data[12 + 4 * (data[0] & 0x0F) :], self._codec):
            self._keyframes = (self._keyframes + [arrival])[-6:]
        self._packets += 1
        self._bytes += len(data)
        if ssrc != self._ssrc:
            if self._ssrc is not None:
                self._restarted = True
            self._ssrc = ssrc
            self._keyframes = self._keyframes[-1:] if self._keyframes and self._keyframes[-1] == arrival else []
            self._max_seq = seq
            self._transit = None
            self._expected += 1
            return
        delta = (seq - self._max_seq) & 0xFFFF
        if 0 < delta < 0x8000:  # newer packet; a late duplicate or reordering adds nothing
            self._expected += delta
            self._max_seq = seq
        transit = arrival * CLOCK_HZ - ts
        if self._transit is not None:
            d = abs(transit - self._transit)
            if d < CLOCK_HZ * 10:  # ignore timestamp jumps
                self._jitter += (d - self._jitter) / 16
        self._transit = transit

    def _keyframe_interval(self):
        """Seconds between full frames: how long a re-opened player waits for a picture."""
        if len(self._keyframes) < 2:
            return None
        gaps = [b - a for a, b in zip(self._keyframes, self._keyframes[1:])]
        return round(sum(gaps) / len(gaps), 1)

    def window(self, now: float) -> dict:
        lost = max(0, self._expected - self._packets)
        result = {
            "packets": self._packets,
            "lossPct": round(100.0 * lost / self._expected, 1) if self._expected else 0.0,
            "jitterMs": round(self._jitter * 1000 / CLOCK_HZ, 1),
            "kbps": round(self._bytes * 8 / 1000),
            "restarted": self._restarted,
            "lastPacketAge": round(now - self._last_at, 2) if self._last_at is not None else None,
            "codec": CODEC_NAMES[self._codec],
            "keyframeS": self._keyframe_interval(),
        }
        self._reset_window()
        return result


class RtpRelay:
    """Listens on the camera's push port and forwards every packet to the player."""

    def __init__(self, listen_port: int, forward_port: int, codec: str = "h265", clock=time.monotonic):
        self.listen_port = listen_port
        self.forward_port = forward_port
        self._clock = clock
        self._stats = RtpStats(codec)
        self._lock = threading.Lock()
        self._sock = None
        self._thread = None

    def start(self) -> bool:
        # All interfaces on purpose: the camera pushes from the internet to this PC's public
        # address (the router forwards the port here), exactly like the pre-flight listener.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        except OSError:
            pass
        try:
            sock.bind(("0.0.0.0", self.listen_port))
        except OSError:
            sock.close()
            return False
        self._sock = sock
        self._thread = threading.Thread(target=self._run, name="rtp-relay", daemon=True)
        self._thread.start()
        return True

    def _run(self):
        sock = self._sock
        out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        target = ("127.0.0.1", self.forward_port)
        try:
            while True:
                try:
                    data = sock.recv(65536)
                except OSError:
                    break
                if parse_rtp(data) is None:
                    continue  # the port is open to the internet: only RTP video goes on to the player
                try:
                    out.sendto(data, target)
                except OSError:
                    pass
                with self._lock:
                    self._stats.feed(data, self._clock())
        finally:
            out.close()

    def window(self) -> dict:
        with self._lock:
            return self._stats.window(self._clock())

    def stop(self):
        sock, self._sock = self._sock, None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
        if self._thread is not None:
            self._thread.join(timeout=1)
            self._thread = None
