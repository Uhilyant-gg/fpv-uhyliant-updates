import tempfile
import unittest
from pathlib import Path
import devices as devices_module
import devices_routeaware as module

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        devices_module.DATA=root;devices_module.DB=root/'devices.sqlite3';devices_module.LEGACY_DB=root/'devices.json'
        self.orig_interfaces=devices_module.interfaces;devices_module.interfaces=lambda:[]
    def tearDown(self):devices_module.interfaces=self.orig_interfaces;self.temp.cleanup()
    def test_known_hosts_include_saved_and_last_seen(self):
        d=module.Devices();d.addDevice('Camera','OpenIPC','192.168.1.40',80,'Network','');d._remember_host('192.168.1.50',True)
        self.assertIn('192.168.1.40',d._known_hosts());self.assertIn('192.168.1.50',d._known_hosts())
    def test_manual_ip_is_remembered_even_when_camera_temporarily_offline(self):
        d=module.Devices();d._remember_host('192.168.1.50',False);self.assertIn('192.168.1.50',d._known_hosts())
    def test_invalid_history_host_is_not_saved(self):
        d=module.Devices();d._remember_host('not-an-ip',True);self.assertEqual(d._known_hosts(),[])
    def test_discovered_add_requires_real_openipc_candidate(self):
        d=module.Devices();d._discovered=[{'host':'192.168.1.50','name':'Generic','openipc':False}]
        self.assertEqual(d.addDiscovered('192.168.1.50','Generic',True),'');self.assertEqual(d.count,0)
if __name__=='__main__':unittest.main()
