import tempfile
import unittest
from pathlib import Path
import devices as devices_module

class DevicesPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);devices_module.DATA=root;devices_module.DB=root/"devices.sqlite3";devices_module.LEGACY_DB=root/"devices.json";self.original_interfaces=devices_module.interfaces;devices_module.interfaces=lambda:[]
    def tearDown(self):
        devices_module.interfaces=self.original_interfaces;self.temp.cleanup()
    def test_active_device_survives_reload_and_delete_clears_setting(self):
        first=devices_module.Devices();device_id=first.addDevice("Camera","OpenIPC","192.168.1.10",80,"Network","");first.setActive(device_id);self.assertEqual(first.activeName,"Camera")
        second=devices_module.Devices();self.assertEqual(second.activeName,"Camera");second.removeDevice(device_id)
        third=devices_module.Devices();self.assertEqual(third.activeName,"");self.assertEqual(third.count,0)
    def test_generic_device_has_no_verified_openipc_identity(self):
        model=devices_module.Devices();device_id=model.addDevice("ONVIF camera","Camera","192.168.1.20",80,"Network","");item=next(i for i in model.items if i["id"]==device_id)
        self.assertFalse(item["openipcIdentity"]["verified"]);self.assertEqual(item["openipcIdentity"]["sensor"],"")
    def test_verified_discovery_identity_is_persisted(self):
        model=devices_module.Devices();model._discovered=[{"host":"192.168.1.30","name":"OpenIPC camera","openipc":True,"evidence":["Majestic /api/v1/config.json"],"identity":{"platform":"ssc30kq","sensor":"imx335","firmware":"2.4"}}]
        device_id=model.addDiscovered("192.168.1.30","OpenIPC camera",True);self.assertTrue(device_id)
        reloaded=devices_module.Devices();item=next(i for i in reloaded.items if i["id"]==device_id);self.assertTrue(item["openipcIdentity"]["verified"]);self.assertEqual(item["openipcIdentity"]["platform"],"ssc30kq");self.assertEqual(item["openipcIdentity"]["sensor"],"imx335")
    def test_snapshot_preserves_separate_entities_and_validates_references(self):
        model=devices_module.Devices();device_id=model.addDevice('Camera','Camera','192.168.1.40',80,'Network','');model.setActive(device_id);snapshot=model.exportSnapshot();self.assertTrue(model.validateSnapshot(snapshot));self.assertEqual(snapshot['activeDeviceId'],device_id);self.assertIn('videoProfiles',snapshot);self.assertIn('openipcIdentities',snapshot)
        bad=dict(snapshot);bad['activeDeviceId']='missing';self.assertFalse(model.validateSnapshot(bad))

if __name__=="__main__":unittest.main()
