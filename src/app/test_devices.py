import tempfile,unittest
from pathlib import Path
import devices as devices_module
class Tests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);devices_module.DATA=root;devices_module.DB=root/'devices.sqlite3';devices_module.LEGACY_DB=root/'devices.json';self.orig=devices_module.interfaces;devices_module.interfaces=lambda:[]
 def tearDown(self):devices_module.interfaces=self.orig;self.temp.cleanup()
 def test_snapshot_and_transactional_restore(self):
  d=devices_module.Devices();did=d.addDevice('Camera','Camera','192.168.1.40',80,'Network','');d.setActive(did);snap=d.exportSnapshot();self.assertTrue(d.validateSnapshot(snap));d.removeDevice(did);self.assertEqual(d.count,0);self.assertTrue(d.restoreSnapshot(snap));self.assertEqual(d.count,1);self.assertEqual(d.activeName,'Camera')
 def test_invalid_snapshot_leaves_live_state_unchanged(self):
  d=devices_module.Devices();did=d.addDevice('Camera','Camera','192.168.1.40',80,'Network','');before=d.exportSnapshot();bad=dict(before);bad['activeDeviceId']='missing';self.assertFalse(d.restoreSnapshot(bad));self.assertEqual(d.exportSnapshot(),before)
 def test_failed_transaction_rolls_back(self):
  d=devices_module.Devices();did=d.addDevice('Camera','Camera','192.168.1.40',80,'Network','');before=d.exportSnapshot();bad={k:(list(v) if isinstance(v,list) else v) for k,v in before.items()};bad['devices']=[dict(bad['devices'][0])];bad['devices'][0]['port']='not-int';self.assertTrue(d.validateSnapshot(bad));self.assertFalse(d.restoreSnapshot(bad));self.assertEqual(d.exportSnapshot(),before)
if __name__=='__main__':unittest.main()
