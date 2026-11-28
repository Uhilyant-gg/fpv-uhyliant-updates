"""Watches the live link in flight by the video frames that actually arrive.

The player's own state is not enough: with video pushed over UDP the player keeps
"playing" when packets stop. So the monitor counts frames from the video sink and
declares the link lost when none arrived for a moment, tells for how long, and
says when the link is back. Recovery itself is automatic and unlimited.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot
from PySide6.QtMultimedia import QVideoSink

LOST_AFTER_S = 1.5
# The first frame after entering the flight screen may take a few seconds.
STARTUP_GRACE_S = 8.0
RESTORED_SHOWN_S = 3.0
# With UDP push the player reports no error when packets stop, so while the link
# is lost the monitor itself asks to re-open the video this often.
RETRY_EVERY_S = 3.0


class LinkMonitor(QObject):
    changed = Signal()
    retryNeeded = Signal()

    def __init__(self, clock=time.monotonic, tick_ms=500):
        super().__init__()
        self._clock = clock
        self._sink = None
        self._active = False
        self._last_frame = None
        self._lost_since = None
        self._restored_at = None
        self._seen_frame = False
        self._last_retry = None
        self._timer = QTimer(self)
        self._timer.setInterval(tick_ms)
        self._timer.timeout.connect(self.evaluate)

    @Property(bool, notify=changed)
    def lost(self):
        return self._lost_since is not None

    @Property(int, notify=changed)
    def lostSeconds(self):
        return int(self._clock() - self._lost_since) if self._lost_since is not None else 0

    @Property(bool, notify=changed)
    def justRestored(self):
        return self._restored_at is not None and self._clock() - self._restored_at < RESTORED_SHOWN_S

    @Property(str, notify=changed)
    def text(self):
        if self.lost:
            return f"Зв’язок із камерою втрачено · {self.lostSeconds} с · відновлюю автоматично"
        if self.justRestored:
            return "Зв’язок відновлено"
        return ""

    @Slot(QVideoSink)
    def setVideoSink(self, sink):
        if sink is self._sink:
            return
        if self._sink is not None:
            try:
                self._sink.videoFrameChanged.disconnect(self._frame)
            except (RuntimeError, TypeError):
                pass
        self._sink = sink
        if sink is not None:
            sink.videoFrameChanged.connect(self._frame)

    @Slot(bool)
    def setActive(self, active):
        """In flight the link is watched; on the home screen it is not."""
        active = bool(active)
        if active == self._active:
            return
        self._active = active
        self._last_frame = self._clock() if active else None
        self._seen_frame = False
        self._lost_since = None
        self._restored_at = None
        self._last_retry = None
        if active:
            self._timer.start()
        else:
            self._timer.stop()
        self.changed.emit()

    def _frame(self, *_):
        self._last_frame = self._clock()
        self._seen_frame = True
        if self._lost_since is not None:
            self._lost_since = None
            self._restored_at = self._clock()
            self.changed.emit()

    @Slot()
    def evaluate(self):
        if not self._active:
            return
        now = self._clock()
        limit = LOST_AFTER_S if self._seen_frame else STARTUP_GRACE_S
        if self._lost_since is None and now - self._last_frame > limit:
            self._lost_since = self._last_frame
            self._last_retry = now
            self.retryNeeded.emit()
        elif self._lost_since is not None and now - self._last_retry >= RETRY_EVERY_S:
            self._last_retry = now
            self.retryNeeded.emit()
        if self._restored_at is not None and now - self._restored_at >= RESTORED_SHOWN_S:
            self._restored_at = None
        self.changed.emit()
