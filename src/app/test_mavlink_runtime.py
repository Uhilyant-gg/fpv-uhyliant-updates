import unittest
import time
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication
from mavlink_runtime import MavlinkRuntime,MavlinkWorker
_app=QCoreApplication.instance() or QCoreApplication([])
class Tests(unittest.TestCase):
 def test_snapshot_marks_stale_fields_while_other_telemetry_remains_current(self):
  worker=MavlinkWorker('udpin:0.0.0.0:14550',115200);now=time.monotonic();worker._last_heartbeat=now;worker._seen.update({'heartbeat':now,'battery':now-6,'gps':now});worker._data.update({'batteryVoltage':12.3,'gpsFix':3});stale=worker._snapshot();self.assertTrue(stale['connected']);self.assertFalse(stale['freshness']['batteryVoltage']);self.assertIsNone(stale['batteryVoltage']);self.assertTrue(stale['freshness']['gpsFix']);self.assertEqual(stale['gpsFix'],3)
 def test_runtime_can_defer_worker_until_qt_startup_completes(self):
  with patch.object(MavlinkRuntime,'start') as start:
   runtime=MavlinkRuntime(auto_start=False);start.assert_not_called();self.assertIsNone(runtime._worker)
 def test_explicit_start_respects_disabled_setting(self):
  runtime=MavlinkRuntime(auto_start=False);runtime._enabled=False
  with patch('mavlink_runtime.MavlinkWorker') as worker:
   runtime.start();worker.assert_not_called()
if __name__=='__main__':unittest.main()
