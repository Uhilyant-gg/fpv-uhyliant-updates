import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
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
    def test_invalid_or_non_private_history_host_is_not_saved(self):
        d=module.Devices()
        for host in ('not-an-ip','8.8.8.8','100.64.1.2','127.0.0.1','169.254.2.3'):d._remember_host(host,True)
        self.assertEqual(d._known_hosts(),[])
    def test_stale_unsafe_history_rows_are_filtered_from_reconnect_candidates(self):
        d=module.Devices()
        with d._connect() as db:
            db.execute("INSERT INTO discovery_history(host,last_seen,openipc) VALUES('8.8.8.8',1,1)")
            db.execute("INSERT INTO discovery_history(host,last_seen,openipc) VALUES('192.168.1.50',2,1)")
        self.assertEqual(d._known_hosts(),['192.168.1.50'])
    def test_discovered_add_requires_real_openipc_candidate(self):
        d=module.Devices();d._discovered=[{'host':'192.168.1.50','name':'Generic','openipc':False}]
        self.assertEqual(d.addDiscovered('192.168.1.50','Generic',True),'');self.assertEqual(d.count,0)
    @patch('devices_routeaware.fingerprint')
    def test_authenticated_add_requires_verified_identity(self,fingerprint):
        d=module.Devices();fingerprint.return_value={'host':'192.168.1.50','camera':True,'openipc':True,'identityVerified':False,'identity':{'verified':True},'evidence':[],'streams':[]}
        self.assertEqual(d.authenticateAndAdd('192.168.1.50','Camera','root','secret'),'');self.assertEqual(d.count,0);self.assertIn('OpenIPC не підтверджено',d.manualError)
    @patch('devices_routeaware.fingerprint')
    def test_authenticated_add_passes_credentials_only_to_probe_and_persists_no_secret(self,fingerprint):
        d=module.Devices();fingerprint.return_value={'host':'192.168.1.50','camera':True,'openipc':True,'identityVerified':True,'identity':{'verified':True,'platform':'ssc30kq','soc':'','sensor':'imx335','firmware':'v1','majestic':'','evidence':['observed']},'evidence':['observed'],'streams':[]}
        did=d.authenticateAndAdd('192.168.1.50','Camera','root','session-secret')
        self.assertTrue(did);fingerprint.assert_called_once();args=fingerprint.call_args.args;self.assertEqual(args[2:4],('root','session-secret'))
        saved=next(item for item in d.items if item['id']==did);self.assertNotIn('password',saved);self.assertNotIn('username',saved);self.assertNotIn('session-secret',repr(saved));self.assertNotIn('session-secret',repr(d.manualResult))
if __name__=='__main__':unittest.main()
