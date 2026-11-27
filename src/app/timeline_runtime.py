from datetime import datetime
import time
from PySide6.QtCore import QObject, Property, QSettings, Signal, Slot


EVENTS = {
    "station-started": ("Станцію запущено", "info"),
    "camera-selected": ("Вибрано камеру", "info"),
    "primary-video-started": ("Основний відеопотік запущено", "info"),
    "primary-video-stopped": ("Основний відеопотік зупинено", "warning"),
    "secondary-video-started": ("Додатковий відеопотік запущено", "info"),
    "secondary-video-stopped": ("Додатковий відеопотік зупинено", "warning"),
    "telemetry-connected": ("Телеметрію підключено", "info"),
    "telemetry-lost": ("Зв’язок із телеметрією втрачено", "warning"),
    "network-ready": ("Мережеве з’єднання підтверджено", "info"),
    "network-degraded": ("Стан мережі погіршився", "warning"),
    "network-lost": ("Мережеве з’єднання недоступне", "warning"),
    "navigation-ready": ("Зовнішню навігацію підтверджено", "info"),
    "navigation-degraded": ("Якість зовнішньої навігації погіршилась", "warning"),
    "navigation-lost": ("Зовнішня навігація недоступна", "warning"),
    "device-discovery-started": ("Пошук пристроїв розпочато", "info"),
    "device-discovery-completed": ("Пошук пристроїв завершено", "info"),
    "device-discovery-cancelled": ("Пошук пристроїв скасовано", "warning"),
    "device-discovery-failed": ("Не вдалося завершити пошук пристроїв", "warning"),
    "app-update-available": ("Знайдено оновлення програми", "info"),
    "app-update-ready": ("Оновлення програми підготовлено", "info"),
    "app-update-installing": ("Встановлення оновлення розпочато", "info"),
    "app-update-failed": ("Не вдалося завершити оновлення програми", "warning"),
}
STATE_EVENTS = {
    "telemetry": {
        "connected": "telemetry-connected",
        "lost": "telemetry-lost",
    },
    "network": {
        "ready": "network-ready",
        "degraded": "network-degraded",
        "lost": "network-lost",
    },
    "navigation": {
        "ready": "navigation-ready",
        "degraded": "navigation-degraded",
        "lost": "navigation-lost",
    },
    "primary-video": {
        "playing": "primary-video-started",
        "stopped": "primary-video-stopped",
    },
    "secondary-video": {
        "playing": "secondary-video-started",
        "stopped": "secondary-video-stopped",
    },
    "discovery": {
        "scanning": "device-discovery-started",
        "completed": "device-discovery-completed",
        "cancelled": "device-discovery-cancelled",
        "failed": "device-discovery-failed",
    },
    "update": {
        "available": "app-update-available",
        "ready": "app-update-ready",
        "installing": "app-update-installing",
        "error": "app-update-failed",
        "blocked": "app-update-failed",
    },
}


class TimelineRuntime(QObject):
    changed = Signal()
    SETTINGS_KEY = "timeline/events"
    MAX_HISTORY = 200
    RETENTION_SECONDS = 30 * 24 * 60 * 60

    def __init__(self, settings=None, clock=time.time):
        super().__init__()
        self._settings = settings or QSettings("FPV-Uhyliant", "FPV-Uhyliant")
        self._clock = clock
        self._last_states = {}
        self._persistence_error = ""
        self._history = self._read_history()
        self.recordEvent("station-started")

    def _read_history(self):
        stored = self._settings.value(self.SETTINGS_KEY, [])
        if not isinstance(stored, (list, tuple)):
            stored = []
        now = int(self._clock())
        cutoff = now - self.RETENTION_SECONDS
        history = []
        for event in stored:
            if not isinstance(event, dict):
                continue
            message = event.get("message")
            timestamp = event.get("timestamp")
            if message not in EVENTS or not isinstance(timestamp, int):
                continue
            if timestamp < cutoff or timestamp > now + 300:
                continue
            history.append({"timestamp": timestamp, "message": message})
        return history[-self.MAX_HISTORY:]

    def _save_history(self):
        self._settings.setValue(self.SETTINGS_KEY, self._history)
        self._settings.sync()
        if self._settings.status() == QSettings.Status.NoError:
            self._persistence_error = ""
        else:
            self._persistence_error = "Не вдалося зберегти історію подій. Поточна сесія залишається доступною."
        self.changed.emit()

    @Property("QVariantList", notify=changed)
    def items(self):
        visible = []
        for event in reversed(self._history):
            presentation = EVENTS.get(event.get("message"))
            if presentation is None:
                continue
            title, level = presentation
            visible.append({
                "time": datetime.fromtimestamp(event["timestamp"]).strftime("%H:%M"),
                "title": title,
                "level": level,
            })
        return visible

    @Property(str, notify=changed)
    def persistenceError(self):
        return self._persistence_error

    @Slot(str, result=bool)
    def recordEvent(self, event_type):
        if event_type not in EVENTS:
            return False
        self._history.append({"timestamp": int(self._clock()), "message": event_type})
        self._history = self._history[-self.MAX_HISTORY:]
        self._save_history()
        return True

    @Slot()
    def clearHistory(self):
        self._history = []
        self._save_history()

    @Slot(str, str)
    def observe(self, source, state):
        state_events = STATE_EVENTS.get(source)
        if state_events is None or state not in {"connected", "ready", "degraded", "lost", "playing", "stopped", "scanning", "completed", "cancelled", "failed", "available", "installing", "error", "blocked", "current", "unknown"}:
            return
        previous = self._last_states.get(source)
        self._last_states[source] = state
        if previous == state:
            return
        if previous in {None, "unknown"} and state in {"lost", "stopped", "unknown"}:
            return
        event_type = state_events.get(state)
        if event_type:
            self.recordEvent(event_type)
