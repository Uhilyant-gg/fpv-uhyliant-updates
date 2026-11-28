"""Names the cause when the flight video is lost or degraded, in plain words.

The chain is camera → (Starlink / ZeroTier / internet) → the pilot's PC → decoder.
Each link has its own sign, and the first broken one is the cause:
- the pilot's PC has no internet;
- packets arrive but no picture (decoder waits for a full frame);
- the camera answers on the network but sends no video;
- the camera does not answer at all (and through what).
While the video plays, packet loss and uneven arrival are warned about early.
"""

from __future__ import annotations

import socket
import threading
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

LOSS_WARN_PCT = 3.0
JITTER_WARN_MS = 30.0
INTERNET_EVERY_S = 3.0
PROBE_WHEN_LOST_EVERY_S = 2.0
INTERNET_HOSTS = (("1.1.1.1", 443), ("8.8.8.8", 53), ("9.9.9.9", 443))

CAMERA_UNREACHABLE = {
    "starlink": "Камера не відповідає · ймовірно, зник зв’язок Starlink на дроні",
    "cloud": "Камера не відповідає через ZeroTier",
    "local": "Камера не відповідає в локальній мережі",
}


def internet_reachable(hosts=INTERNET_HOSTS, timeout=1.5, connect=socket.create_connection) -> bool:
    for host, port in hosts:
        try:
            connect((host, port), timeout=timeout).close()
            return True
        except OSError:
            continue
    return False


def diagnose(kind, lost, stream=None, internet=None, camera_reachable=None) -> dict:
    """(code, level, text). ``stream`` is the relay window for pushed video, else None."""
    stream = stream or {}
    if lost:
        if internet is False and kind != "local":
            return {"code": "pc-offline", "level": "lost", "text": "Пропав інтернет на ПК пілота"}
        if stream.get("packets"):
            return {
                "code": "no-picture",
                "level": "lost",
                "text": "Відео приходить, але не показується · чекаю повного кадру",
            }
        if camera_reachable is True:
            return {"code": "camera-silent", "level": "lost", "text": "Камера на зв’язку, але не надсилає відео"}
        if kind == "static":
            return {"code": "no-packets", "level": "lost", "text": "Від камери не надходить жодного пакета відео"}
        if camera_reachable is False and kind in CAMERA_UNREACHABLE:
            return {"code": "camera-unreachable", "level": "lost", "text": CAMERA_UNREACHABLE[kind]}
        return {"code": "checking", "level": "lost", "text": "Визначаю причину…"}
    loss = float(stream.get("lossPct") or 0)
    if loss >= LOSS_WARN_PCT:
        return {
            "code": "loss",
            "level": "warning",
            "text": f"Втрачається {loss:g}% пакетів · канал перевантажений".replace(".", ","),
        }
    if float(stream.get("jitterMs") or 0) >= JITTER_WARN_MS:
        return {"code": "jitter", "level": "warning", "text": "Відео приходить нерівно · можливі посмикування"}
    return {"code": "ok", "level": "ok", "text": ""}


class LinkDoctor(QObject):
    changed = Signal()
    retryNeeded = Signal()
    _internetChecked = Signal(bool)

    def __init__(
        self,
        link_monitor,
        devices,
        connections,
        internet_check=internet_reachable,
        run_async=True,
        clock=time.monotonic,
        tick_ms=1000,
    ):
        super().__init__()
        self._monitor = link_monitor
        self._devices = devices
        self._connections = connections
        self._internet_check = internet_check
        self._run_async = run_async
        self._clock = clock
        self._active = False
        self._internet = None
        self._internet_at = None
        self._internet_busy = False
        self._probe_at = None
        self._stream = None
        self._verdict = diagnose("", False)
        self._internetChecked.connect(self._apply_internet)
        self._timer = QTimer(self)
        self._timer.setInterval(tick_ms)
        self._timer.timeout.connect(self.evaluate)

    @Property(str, notify=changed)
    def code(self):
        return self._verdict["code"]

    @Property(str, notify=changed)
    def level(self):
        return self._verdict["level"]

    @Property(str, notify=changed)
    def text(self):
        return self._verdict["text"]

    @Property("QVariantMap", notify=changed)
    def details(self):
        stream = self._stream or {}
        return {
            "internet": self._internet,
            "hasStream": self._stream is not None,
            "lossPct": stream.get("lossPct", 0.0),
            "jitterMs": stream.get("jitterMs", 0.0),
            "kbps": stream.get("kbps", 0),
        }

    @Slot(bool)
    def setActive(self, active):
        active = bool(active)
        if active == self._active:
            return
        self._active = active
        self._internet = None
        self._internet_at = None
        self._probe_at = None
        self._stream = None
        self._verdict = diagnose("", False)
        if active:
            self._timer.start()
        else:
            self._timer.stop()
        self.changed.emit()

    def _device_and_kind(self):
        device_id = getattr(self._devices, "activeId", "") or ""
        return device_id, (self._connections.selected.get(device_id, "") if device_id else "")

    def _camera_reachable(self, device_id, kind):
        if kind not in CAMERA_UNREACHABLE:
            return None  # with a static IP the camera sends, nobody pings it: packets are the only sign
        entry = self._connections.statuses.get(device_id, {}).get(kind, {})
        state = entry.get("state")
        return True if state == "available" else (False if state == "unavailable" else None)

    @Slot()
    def evaluate(self):
        if not self._active:
            return
        now = self._clock()
        device_id, kind = self._device_and_kind()
        self._stream = self._connections.relay_window(device_id) if device_id else None
        if self._stream and self._stream.get("restarted"):
            # The camera restarted its stream: the player must re-open it, at once.
            self.retryNeeded.emit()
        if kind != "local" and (self._internet_at is None or now - self._internet_at >= INTERNET_EVERY_S):
            self._check_internet(now)
        lost = bool(self._monitor.lost)
        if lost and kind in ("local", "starlink", "cloud"):
            if self._probe_at is None or now - self._probe_at >= PROBE_WHEN_LOST_EVERY_S:
                self._probe_at = now
                self._connections.probeSelected(device_id)
        reachable = self._camera_reachable(device_id, kind) if kind else None
        self._verdict = diagnose(kind, lost, self._stream, self._internet, reachable)
        self.changed.emit()

    def _check_internet(self, now):
        if self._internet_busy:
            return
        self._internet_busy = True
        self._internet_at = now

        def work():
            try:
                ok = bool(self._internet_check())
            except Exception:
                ok = False
            self._internetChecked.emit(ok)

        if self._run_async:
            threading.Thread(target=work, name="internet-check", daemon=True).start()
        else:
            work()

    def _apply_internet(self, ok):
        self._internet_busy = False
        if self._active:
            self._internet = ok
