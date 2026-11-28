"""The Starlink dish on the drone, watched in flight through the camera.

Every few seconds the station asks the dish for its state (latency, loss,
obstruction, alerts). The dish can only be reached while the link works, so the
cause of a dropout is told right after the link is back, from the dish's own
per-second history ("перешкода в небі", "немає супутника", …).
"""

from __future__ import annotations

import threading
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

import starlink_dish as sd

POLL_MS = 3000


class StarlinkRuntime(QObject):
    changed = Signal()
    _status = Signal(object)
    _cause = Signal(str)

    def __init__(self, devices, connections, shell_for, run_async=True, poll_ms=POLL_MS, clock=time.monotonic):
        super().__init__()
        self._devices = devices
        self._connections = connections
        self._shell_for = shell_for  # host -> CameraShell (context manager with open_tcp)
        self._run_async = run_async
        self._clock = clock
        self._active = False
        self._busy = False
        self._session = None
        self._session_host = ""
        self._lock = threading.Lock()
        self._data: dict = {}
        self._available = False
        self._reason = ""
        self._last_cause = ""
        self._status.connect(self._apply)
        self._cause.connect(self._apply_cause)
        self._timer = QTimer(self)
        self._timer.setInterval(poll_ms)
        self._timer.timeout.connect(self.poll)

    # --- properties ------------------------------------------------------------
    @Property(bool, notify=changed)
    def available(self):
        return self._available

    @Property("QVariantMap", notify=changed)
    def status(self):
        return dict(self._data)

    @Property(str, notify=changed)
    def reason(self):
        """Why there is no dish data, in plain words."""
        return self._reason

    @Property(str, notify=changed)
    def lastOutageCause(self):
        return self._last_cause

    def warning(self) -> str:
        """A problem the dish reports while the video still plays (for the link doctor)."""
        if not self._available:
            return ""
        if self._data.get("currentlyObstructed"):
            return "Starlink: перешкода в небі зараз"
        alerts = self._data.get("alerts") or []
        return f"Starlink: {alerts[0]}" if alerts else ""

    # --- control ---------------------------------------------------------------
    @Slot(bool)
    def setActive(self, active):
        self._active = bool(active)
        if self._active:
            self._timer.start()
            self.poll()
        else:
            self._timer.stop()
            self._close()

    def _host(self):
        device_id = getattr(self._devices, "activeId", "") or ""
        return self._connections.control_host(device_id) if device_id else ""

    def _run(self, work):
        if self._run_async:
            threading.Thread(target=work, name="starlink-dish", daemon=True).start()
        else:
            work()

    def _with_session(self, host, action):
        """Keep one SSH session to the camera between reads; reopen it after a failure."""
        with self._lock:
            if self._session is None or self._session_host != host:
                self._close_locked()
                shell = self._shell_for(host)
                self._session = shell.__enter__()
                self._session_host = host
            session = self._session
        try:
            return action(session)
        except Exception:
            self._close()
            raise

    def _close(self):
        with self._lock:
            self._close_locked()

    def _close_locked(self):
        if self._session is not None:
            try:
                self._session.__exit__(None, None, None)
            except Exception:
                pass
        self._session = None
        self._session_host = ""

    @Slot()
    def poll(self):
        if self._busy:
            return
        host = self._host()
        if not host:
            self._apply({"error": "Антену видно лише через ZeroTier або локальну мережу камери"})
            return
        self._busy = True

        def work():
            try:
                message = self._with_session(host, lambda s: sd.call(s.open_tcp, sd.GET_STATUS, sd.DISH_GET_STATUS))
                result = sd.status(message)
            except Exception:
                result = {"error": "Антена Starlink не відповідає через камеру"}
            self._status.emit(result)

        self._run(work)

    def _apply(self, result):
        self._busy = False
        if "error" in result:
            self._available, self._reason = False, result["error"]
        else:
            self._available, self._reason, self._data = True, "", result
        self.changed.emit()

    @Slot(int)
    def explainOutage(self, seconds):
        """Right after the link is back: ask the dish what happened during the last ``seconds``."""
        host = self._host()
        if not host or seconds <= 0:
            return

        def work():
            try:
                message = self._with_session(host, lambda s: sd.call(s.open_tcp, sd.GET_HISTORY, sd.DISH_GET_HISTORY))
                cause = sd.outage_cause(sd.history(message), seconds + 2)
            except Exception:
                cause = ""
            self._cause.emit(cause)

        self._run(work)

    def _apply_cause(self, cause):
        self._last_cause = cause
        self.changed.emit()
