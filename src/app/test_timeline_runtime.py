import unittest

from PySide6.QtCore import QSettings
from timeline_runtime import TimelineRuntime


class Settings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass

    def status(self):
        return QSettings.Status.NoError


class TimelineRuntimeTests(unittest.TestCase):
    def test_timeline_uses_human_copy_and_excludes_internal_events(self):
        timeline = TimelineRuntime(Settings(), clock=lambda: 60)

        self.assertEqual(timeline.items[0]["title"], "Станцію запущено")
        self.assertEqual(timeline.items[0]["level"], "info")
        self.assertFalse(timeline.recordEvent("raw transport exception"))
        self.assertNotIn("raw transport exception", repr(timeline.items))

    def test_state_changes_are_deduplicated_and_initial_absence_is_not_an_alert(self):
        timeline = TimelineRuntime(Settings(), clock=lambda: 120)
        timeline.observe("telemetry", "unknown")
        timeline.observe("telemetry", "lost")
        timeline.observe("telemetry", "connected")
        timeline.observe("telemetry", "connected")
        timeline.observe("telemetry", "lost")

        self.assertEqual(
            [item["title"] for item in timeline.items],
            ["Зв’язок із телеметрією втрачено", "Телеметрію підключено", "Станцію запущено"],
        )

    def test_device_discovery_lifecycle_is_human_readable_and_deduplicated(self):
        timeline = TimelineRuntime(Settings(), clock=lambda: 180)
        for state in ("unknown", "scanning", "scanning", "completed", "completed", "scanning", "failed", "failed", "scanning", "cancelled", "cancelled"):
            timeline.observe("discovery", state)

        self.assertEqual(
            [item["title"] for item in timeline.items],
            [
                "Пошук пристроїв скасовано",
                "Пошук пристроїв розпочато",
                "Не вдалося завершити пошук пристроїв",
                "Пошук пристроїв розпочато",
                "Пошук пристроїв завершено",
                "Пошук пристроїв розпочато",
                "Станцію запущено",
            ],
        )

    def test_application_update_lifecycle_records_only_meaningful_states(self):
        timeline = TimelineRuntime(Settings(), clock=lambda: 240)
        for state in ("check", "available", "available", "download", "ready", "installing", "blocked", "blocked"):
            timeline.observe("update", state)

        self.assertEqual(
            [item["title"] for item in timeline.items],
            [
                "Не вдалося завершити оновлення програми",
                "Встановлення оновлення розпочато",
                "Оновлення програми підготовлено",
                "Знайдено оновлення програми",
                "Станцію запущено",
            ],
        )

    def test_device_changes_and_restore_have_safe_timeline_copy(self):
        timeline = TimelineRuntime(Settings(), clock=lambda: 300)
        for event_type in ("device-added", "device-updated", "device-removed", "device-list-restored"):
            self.assertTrue(timeline.recordEvent(event_type))

        self.assertEqual(
            [item["title"] for item in timeline.items],
            [
                "Список пристроїв відновлено",
                "Пристрій видалено",
                "Налаштування пристрою змінено",
                "Пристрій додано",
                "Станцію запущено",
            ],
        )

    def test_new_events_notify_timeline_consumers(self):
        timeline = TimelineRuntime(Settings(), clock=lambda: 120)
        changes = []
        timeline.changed.connect(lambda: changes.append(True))

        timeline.recordEvent("camera-selected")

        self.assertEqual(changes, [True])

    def test_history_is_persisted_without_details_and_can_be_cleared(self):
        settings = Settings()
        timeline = TimelineRuntime(settings, clock=lambda: 120)
        timeline.recordEvent("camera-selected")

        restored = TimelineRuntime(settings, clock=lambda: 180)

        self.assertEqual(
            [item["title"] for item in restored.items],
            ["Станцію запущено", "Вибрано камеру", "Станцію запущено"],
        )
        self.assertEqual(
            set(settings.value(TimelineRuntime.SETTINGS_KEY)[-1]),
            {"timestamp", "message"},
        )
        restored.clearHistory()
        self.assertEqual(restored.items, [])

    def test_history_is_pruned_to_retention_window_and_entry_limit(self):
        now = TimelineRuntime.RETENTION_SECONDS + 100
        settings = Settings()
        settings.values[TimelineRuntime.SETTINGS_KEY] = [
            {"timestamp": 0, "message": "camera-selected"},
            {"timestamp": now, "message": "camera-selected"},
            {"timestamp": now + 301, "message": "video-started"},
            {"timestamp": now, "message": "unrecognized"},
        ]
        timeline = TimelineRuntime(settings, clock=lambda: now)

        self.assertEqual(
            [item["title"] for item in timeline.items],
            ["Станцію запущено", "Вибрано камеру"],
        )
        for _ in range(TimelineRuntime.MAX_HISTORY + 10):
            timeline.recordEvent("camera-selected")
        self.assertEqual(len(timeline.items), TimelineRuntime.MAX_HISTORY)
        self.assertEqual(len(settings.value(TimelineRuntime.SETTINGS_KEY)), TimelineRuntime.MAX_HISTORY)


if __name__ == "__main__":
    unittest.main()
