"""Sound from the camera's microphone, played on the station in flight.

The camera (majestic Lite/Ultimate) gives its microphone over HTTP. The station
takes the A-law stream (/audio.alaw: 8 bits a sample, so 64 kbit/s at 8 kHz, the
cheapest for the link) and falls back to raw PCM (/audio.pcm). Samples are
played as soon as they arrive; when the PC falls behind, old samples are dropped
so the sound never lags behind the picture. After a dropout the sound comes back
by itself.

Only cameras on the station's own networks are asked (private addresses).
"""

from __future__ import annotations

import base64
import http.client
import ipaddress
import json
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

PATHS = (("/audio.alaw", "alaw"), ("/audio.pcm", "pcm"))
CHUNK = 256
RETRY_MS = 2000
# How much sound may wait in the PC's buffer; more is dropped (it would lag behind the video).
MAX_BUFFER_S = 0.12


def _alaw_sample(value: int) -> int:
    value ^= 0x55
    sign = value & 0x80
    exponent = (value >> 4) & 0x07
    mantissa = value & 0x0F
    sample = (mantissa << 4) + 8
    if exponent:
        sample = (sample + 0x100) << (exponent - 1)
    return sample if sign else -sample


_ALAW = b"".join(_alaw_sample(i).to_bytes(2, "little", signed=True) for i in range(256))


def alaw_to_pcm(data: bytes) -> bytes:
    """G.711 A-law bytes to 16-bit little-endian samples."""
    return b"".join(_ALAW[2 * b : 2 * b + 2] for b in data)


def http_host(host: str) -> str:
    return f"[{host}]" if ":" in host else host


def open_stream(host, path, login=None, timeout=5.0):
    """GET a majestic audio endpoint; (status, response). Only private addresses."""
    if not ipaddress.ip_address(host).is_private:
        raise PermissionError("not a private address")
    connection = http.client.HTTPConnection(http_host(host), 80, timeout=timeout)
    headers = {}
    if login:
        token = base64.b64encode(f"{login[0]}:{login[1]}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    connection.request("GET", path, headers=headers)
    response = connection.getresponse()
    return response.status, response


def qt_sink(rate):
    """The PC's default sound output, or None when it has none."""
    from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices

    device = QMediaDevices.defaultAudioOutput()
    if device.isNull():
        return None
    fmt = QAudioFormat()
    fmt.setSampleRate(int(rate))
    fmt.setChannelCount(1)
    fmt.setSampleFormat(QAudioFormat.Int16)
    sink = QAudioSink(device, fmt)
    sink.setBufferSize(int(rate * 2 * MAX_BUFFER_S))

    class Sink:
        def __init__(self):
            self.io = sink.start()

        def write(self, pcm):
            # Behind: drop this piece instead of letting the sound lag.
            if sink.bytesFree() >= len(pcm):
                self.io.write(pcm)

        def setVolume(self, volume):
            sink.setVolume(QAudio.convertVolume(volume, QAudio.LogarithmicVolumeScale, QAudio.LinearVolumeScale))

        def stop(self):
            sink.stop()

    return Sink()


class AudioRuntime(QObject):
    changed = Signal()
    _chunk = Signal(int, bytes)
    _ended = Signal(int, str)

    def __init__(
        self,
        devices,
        connections,
        features,
        logins=lambda: [],
        store_path=None,
        opener=open_stream,
        sink_factory=qt_sink,
        run_async=True,
    ):
        super().__init__()
        self._devices = devices
        self._connections = connections
        self._features = features
        self._logins = logins
        self._store = Path(store_path) if store_path else None
        self._opener = opener
        self._sink_factory = sink_factory
        self._run_async = run_async
        self._active = False
        self._generation = 0
        self._sink = None
        self._playing = False
        self._state = "off"
        self._muted, self._volume = self._load()
        self._chunk.connect(self._play)
        self._ended.connect(self._stream_ended)
        self._retry = QTimer(self)
        self._retry.setSingleShot(True)
        self._retry.setInterval(RETRY_MS)
        self._retry.timeout.connect(self._start)
        signal = getattr(features, "changed", None)
        if signal is not None:
            signal.connect(self._features_changed)

    # --- saved choices --------------------------------------------------------------
    def _load(self):
        try:
            data = json.loads(self._store.read_text(encoding="utf-8")) if self._store else {}
        except (OSError, ValueError):
            data = {}
        volume = data.get("volume", 80) if isinstance(data, dict) else 80
        muted = bool(data.get("muted", False)) if isinstance(data, dict) else False
        return muted, max(0, min(100, int(volume))) if isinstance(volume, (int, float)) else 80

    def _save(self):
        if self._store is None:
            return
        try:
            self._store.parent.mkdir(parents=True, exist_ok=True)
            self._store.write_text(json.dumps({"muted": self._muted, "volume": self._volume}), encoding="utf-8")
        except OSError:
            pass

    # --- what QML shows ------------------------------------------------------------
    @Property(bool, notify=changed)
    def available(self):
        return bool(getattr(self._features, "micEnabled", False))

    @Property(bool, notify=changed)
    def playing(self):
        return self._playing

    @Property(bool, notify=changed)
    def muted(self):
        return self._muted

    @Property(int, notify=changed)
    def volume(self):
        return self._volume

    @Property(str, notify=changed)
    def text(self):
        if not getattr(self._features, "audioSupported", False):
            return getattr(self._features, "audioText", "") or "звуку немає"
        if not self.available:
            return "мікрофон камери вимкнено"
        if self._muted:
            return "звук вимкнено на станції"
        return {
            "playing": "звук грає",
            "waiting": "чекаю звук від камери",
            "no-output": "на цьому ПК немає виходу звуку",
            "off": "звук увімкнеться в польоті",
        }.get(self._state, "чекаю звук від камери")

    # --- control -------------------------------------------------------------------
    @Slot(bool)
    def setActive(self, active):
        self._active = bool(active)
        self._restart()

    @Slot()
    def toggleMute(self):
        self.setMuted(not self._muted)

    @Slot(bool)
    def setMuted(self, muted):
        self._muted = bool(muted)
        self._save()
        self._restart()  # a muted stream is stopped: it spends no bitrate

    @Slot(int)
    def setVolume(self, volume):
        self._volume = max(0, min(100, int(volume)))
        if self._sink is not None:
            self._sink.setVolume(self._volume / 100)
        self._save()
        self.changed.emit()

    def _features_changed(self):
        wanted = self._wanted()
        if wanted != (self._state in ("playing", "waiting", "no-output")):
            self._restart()
        else:
            self.changed.emit()

    def _wanted(self):
        return self._active and not self._muted and self.available

    def _restart(self):
        self._stop()
        if self._wanted():
            self._start()
        self.changed.emit()

    def _stop(self):
        self._generation += 1
        self._retry.stop()
        if self._sink is not None:
            try:
                self._sink.stop()
            except Exception:
                pass
        self._sink, self._playing, self._state = None, False, "off"

    def _start(self):
        if not self._wanted():
            return
        device_id = getattr(self._devices, "activeId", "") or ""
        host = self._connections.control_host(device_id) if device_id else ""
        rate = int(getattr(self._features, "micRate", 8000) or 8000)
        if self._sink is None:
            self._sink = self._sink_factory(rate)
            if self._sink is None:
                self._state = "no-output"
                self.changed.emit()
                return
            self._sink.setVolume(self._volume / 100)
        self._state = "waiting"
        self.changed.emit()
        if not host:
            self._retry.start()
            return
        self._generation += 1
        generation = self._generation
        logins = [None] + [tuple(x) for x in self._logins() if x and x[1]]

        def work():
            reason = "failed"
            try:
                for path, kind in PATHS:
                    for login in logins:
                        status, response = self._opener(host, path, login)
                        if status == 401:
                            continue
                        if status != 200:
                            break
                        while generation == self._generation:
                            data = response.read(CHUNK if kind == "alaw" else CHUNK * 2)
                            if not data:
                                break
                            self._chunk.emit(generation, alaw_to_pcm(data) if kind == "alaw" else data)
                        return self._ended.emit(generation, "ended")
            except Exception:
                reason = "failed"
            self._ended.emit(generation, reason)

        if self._run_async:
            threading.Thread(target=work, name="camera-audio", daemon=True).start()
        else:
            work()

    def _play(self, generation, pcm):
        if generation != self._generation or self._sink is None:
            return
        self._sink.write(pcm)
        if not self._playing:
            self._playing, self._state = True, "playing"
            self.changed.emit()

    def _stream_ended(self, generation, _reason):
        if generation != self._generation:
            return
        self._playing, self._state = False, "waiting"
        self.changed.emit()
        if self._wanted():
            self._retry.start()
