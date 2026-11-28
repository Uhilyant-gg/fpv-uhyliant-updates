import json
import unittest

from PySide6.QtCore import QCoreApplication, QObject, QSettings, Signal

from backend import Station
from flight_alerts import DEFAULT_THRESHOLDS
from flight_alerts_runtime import FlightAlertsRuntime


class Settings:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.sync_status = QSettings.NoError

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass

    def status(self):
        return self.sync_status


class Telemetry(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.telemetry = {"connected": None}

    def set(self, **values):
        self.telemetry = values
        self.changed.emit()


class StationThresholdTests(unittest.TestCase):
    def test_defaults_then_persisted_changes_survive_restart(self):
        settings = Settings()
        station = Station(settings)
        self.assertEqual(station.alertThresholds, DEFAULT_THRESHOLDS)
        self.assertTrue(station.setAlertThreshold("linkQualityMin", 65))
        self.assertTrue(station.setAlertThreshold("cellCount", 6))
        self.assertEqual(json.loads(settings.values["alerts/thresholds"])["linkQualityMin"], 65)
        restarted = Station(settings)
        self.assertEqual(restarted.alertThresholds["linkQualityMin"], 65)
        self.assertEqual(restarted.alertThresholds["cellCount"], 6)

    def test_invalid_values_are_rejected_and_reset_restores_defaults(self):
        settings = Settings()
        station = Station(settings)
        self.assertFalse(station.setAlertThreshold("linkQualityMin", 150))
        self.assertFalse(station.setAlertThreshold("nope", 1))
        self.assertEqual(station.alertThresholds, DEFAULT_THRESHOLDS)
        station.setAlertThreshold("batteryRemainingMin", 35)
        self.assertTrue(station.resetAlertThresholds())
        self.assertEqual(Station(settings).alertThresholds, DEFAULT_THRESHOLDS)

    def test_corrupt_stored_thresholds_fall_back_to_defaults(self):
        station = Station(Settings({"alerts/thresholds": "{not json"}))
        self.assertEqual(station.alertThresholds, DEFAULT_THRESHOLDS)

    def test_failed_save_is_reported(self):
        settings = Settings()
        station = Station(settings)
        settings.sync_status = QSettings.AccessError
        self.assertFalse(station.setAlertThreshold("linkQualityMin", 60))


class FlightAlertsRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_alerts_follow_telemetry_and_thresholds(self):
        telemetry = Telemetry()
        station = Station(Settings())
        runtime = FlightAlertsRuntime(telemetry, station)
        self.assertFalse(runtime.active)
        telemetry.set(connected=True, linkQuality=45)
        self.assertTrue(runtime.active)
        self.assertEqual(runtime.level, "critical")
        self.assertIn("LQ 45%", runtime.text)
        station.setAlertThreshold("linkQualityMin", 40)
        self.assertFalse(runtime.active)
        telemetry.set(connected=False)
        self.assertEqual(runtime.text, "Телеметрію втрачено")

    def test_no_lost_banner_for_telemetry_that_never_came(self):
        telemetry = Telemetry()
        runtime = FlightAlertsRuntime(telemetry, Station(Settings()))
        telemetry.set(connected=False)
        self.assertFalse(runtime.active, "a drone without a flight-controller link is not an emergency")
        telemetry.set(connected=True)
        telemetry.set(connected=False)
        self.assertEqual(runtime.text, "Телеметрію втрачено")
        runtime.resetSession()
        self.assertFalse(runtime.active, "a new flight starts clean")


if __name__ == "__main__":
    unittest.main()
