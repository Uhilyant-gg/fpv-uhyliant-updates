import unittest
import time
from types import SimpleNamespace
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication
from mavlink_runtime import MavlinkRuntime, MavlinkWorker, _bearing_deg

_app = QCoreApplication.instance() or QCoreApplication([])


class Tests(unittest.TestCase):
    def test_snapshot_marks_stale_fields_while_other_telemetry_remains_current(self):
        worker = MavlinkWorker('udpin:0.0.0.0:14550', 115200)
        now = time.monotonic()
        worker._last_heartbeat = now
        worker._seen.update({'heartbeat': now, 'battery': now - 6, 'gps': now})
        worker._field_seen.update({'batteryVoltage': now - 6, 'gpsFix': now})
        worker._data.update({'batteryVoltage': 12.3, 'gpsFix': 3})
        stale = worker._snapshot()
        self.assertTrue(stale['connected'])
        self.assertFalse(stale['freshness']['batteryVoltage'])
        self.assertIsNone(stale['batteryVoltage'])
        self.assertTrue(stale['freshness']['gpsFix'])
        self.assertEqual(stale['gpsFix'], 3)

    def test_updates_do_not_refresh_other_fields_in_same_group(self):
        worker = MavlinkWorker('udpin:0.0.0.0:14550', 115200)
        with patch('mavlink_runtime.time.monotonic', return_value=10):
            worker._emit('position', groundSpeed=20.0)
        with patch('mavlink_runtime.time.monotonic', return_value=14):
            worker._emit('position', altitude=100.0)
            snapshot = worker._snapshot()
        self.assertIsNone(snapshot['groundSpeed'])
        self.assertFalse(snapshot['freshness']['groundSpeed'])
        self.assertEqual(snapshot['altitude'], 100.0)
        self.assertTrue(snapshot['freshness']['altitude'])

    def test_bearing_points_from_drone_to_home(self):
        home = (50.0, 30.0)
        self.assertAlmostEqual(_bearing_deg((49.99, 30.0), home), 0.0, places=1)  # home is north
        self.assertAlmostEqual(_bearing_deg((50.0, 30.01), home), 270.0, places=1)  # home is west
        self.assertAlmostEqual(_bearing_deg((50.01, 30.0), home), 180.0, places=1)
        self.assertIsNone(_bearing_deg(None, home))
        self.assertIsNone(_bearing_deg(home, home))  # at home: no direction

    def test_home_bearing_follows_position_and_home(self):
        worker = MavlinkWorker('udpin:0.0.0.0:14550', 115200)
        home = SimpleNamespace(get_type=lambda: 'HOME_POSITION', latitude=500000000, longitude=300000000)
        position = SimpleNamespace(
            get_type=lambda: 'GLOBAL_POSITION_INT', lat=499900000, lon=300000000, relative_alt=50000, hdg=9000
        )
        with (
            patch.object(worker, '_account', return_value=True),
            patch('mavlink_runtime.time.monotonic', return_value=10),
        ):
            worker._handle(position)
            self.assertIsNone(worker._snapshot()['homeBearing'])
            worker._handle(home)
            worker._handle(position)
            snapshot = worker._snapshot()
        self.assertAlmostEqual(snapshot['homeBearing'], 0.0, places=1)
        self.assertAlmostEqual(snapshot['homeDistance'], 1112, delta=5)
        self.assertEqual(snapshot['heading'], 90.0)

    def test_battery_message_without_voltage_does_not_refresh_old_voltage(self):
        worker = MavlinkWorker('udpin:0.0.0.0:14550', 115200)
        with patch('mavlink_runtime.time.monotonic', return_value=10):
            worker._emit('battery', batteryVoltage=12.3)
        msg = SimpleNamespace(
            get_type=lambda: 'BATTERY_STATUS', voltages=[65535], current_battery=100, battery_remaining=80
        )
        with (
            patch.object(worker, '_account', return_value=True),
            patch('mavlink_runtime.time.monotonic', return_value=16),
        ):
            worker._handle(msg)
            snapshot = worker._snapshot()
        self.assertIsNone(snapshot['batteryVoltage'])
        self.assertFalse(snapshot['freshness']['batteryVoltage'])
        self.assertTrue(snapshot['freshness']['current'])
        self.assertEqual(snapshot['current'], 1.0)

    def test_runtime_can_defer_worker_until_qt_startup_completes(self):
        with patch.object(MavlinkRuntime, 'start') as start:
            runtime = MavlinkRuntime(auto_start=False)
            start.assert_not_called()
            self.assertIsNone(runtime._worker)

    def test_explicit_start_respects_disabled_setting(self):
        runtime = MavlinkRuntime(auto_start=False)
        runtime._enabled = False
        with patch('mavlink_runtime.MavlinkWorker') as worker:
            runtime.start()
            worker.assert_not_called()

    def test_current_worker_failure_clears_last_live_values(self):
        runtime = MavlinkRuntime(auto_start=False)
        runtime._telemetry = {'connected': True, 'batteryVoltage': 12.3}
        runtime._on_error(runtime._generation, 'failed')
        self.assertFalse(runtime.telemetry['connected'])
        self.assertNotIn('batteryVoltage', runtime.telemetry)

    def test_outdated_worker_failure_does_not_clear_new_connection(self):
        runtime = MavlinkRuntime(auto_start=False)
        runtime._telemetry = {'connected': True, 'batteryVoltage': 12.3}
        runtime._on_error(runtime._generation - 1, 'old failure')
        self.assertTrue(runtime.telemetry['connected'])
        self.assertEqual(runtime.telemetry['batteryVoltage'], 12.3)


if __name__ == '__main__':
    unittest.main()
