import tempfile
import unittest
from pathlib import Path
import devices as devices_module


class DevicesPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        devices_module.DATA = root
        devices_module.DB = root / "devices.sqlite3"
        devices_module.LEGACY_DB = root / "devices.json"
        self.original_interfaces = devices_module.interfaces
        devices_module.interfaces = lambda: []

    def tearDown(self):
        devices_module.interfaces = self.original_interfaces
        self.temp.cleanup()

    def test_active_device_survives_reload_and_delete_clears_setting(self):
        first = devices_module.Devices()
        device_id = first.addDevice("Camera", "OpenIPC", "192.168.1.10", 80, "Network", "")
        first.setActive(device_id)
        self.assertEqual(first.activeName, "Camera")

        second = devices_module.Devices()
        self.assertEqual(second.activeName, "Camera")
        second.removeDevice(device_id)

        third = devices_module.Devices()
        self.assertEqual(third.activeName, "")
        self.assertEqual(third.count, 0)


if __name__ == "__main__":
    unittest.main()
