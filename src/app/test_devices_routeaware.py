import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import devices as devices_module
import devices_routeaware as module
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);devices_module.DATA=root;devices_module.DB=root/'devices.sqlite3';self.orig=devices_module.interfaces;devices_module.interfaces=lambda:[]
 def tearDown(self):devices_module.interfaces=self.orig;self.temp.cleanup()
 def verified(self):return {'host':'192.168.1.50','camera':True,'openipc':True,'identityVerified':True,'identity':{'verified':True,'platform':'ssc30kq','soc':'ssc338q','sensor':'imx335','firmware':'v1','majestic':'','evidence':['observed']},'evidence':['observed'],'streams':[]}
 def test_known_hosts_include_saved_and_last_seen(self):
  d=module.Devices();d.addDevice('Camera','OpenIPC','192.168.1.40',80,'Network','');d._remember_host('192.168.1.50',True);self.assertIn('192.168.1.40',d._known_hosts());self.assertIn('192.168.1.50',d._known_hosts())
 def test_manual_completion_clears_busy_and_exposes_verified_state(self):
  d=module.Devices();d._manual_busy=True;d._on_manual_done(self.verified(),'');self.assertFalse(d.manualBusy);self.assertEqual(d.manualStatus,'verified');self.assertEqual(d.manualMessage,'OpenIPC підтверджено');self.assertEqual(d.manualResult['identity']['sensor'],'imx335')
 def test_manual_auth_candidate_has_explicit_state(self):
  d=module.Devices();d._manual_busy=True;d._on_manual_done({'host':'192.168.1.50','camera':True,'openipc':False,'identityVerified':False,'authRequired':True},'');self.assertFalse(d.manualBusy);self.assertEqual(d.manualStatus,'auth-required');self.assertIn('логін',d.manualMessage)
 def test_manual_no_camera_has_visible_error_state(self):
  d=module.Devices();d._manual_busy=True;d._on_manual_done({},'');self.assertFalse(d.manualBusy);self.assertEqual(d.manualStatus,'error');self.assertTrue(d.manualError)
 def test_verified_manual_candidate_adds_and_reports_success(self):
  d=module.Devices();d._manual_result=self.verified();did=d.addDiscovered('192.168.1.50','Camera',True);self.assertTrue(did);self.assertEqual(d.count,1);self.assertEqual(d.manualStatus,'added');self.assertIn('додано',d.manualMessage.lower());saved=d.items[0];self.assertTrue(saved['openipcIdentity']['verified']);self.assertEqual(saved['openipcIdentity']['sensor'],'imx335')
 def test_duplicate_add_is_idempotent_and_visible(self):
  d=module.Devices();d._manual_result=self.verified();first=d.addDiscovered('192.168.1.50','Camera',True);second=d.addDiscovered('192.168.1.50','Camera',True);self.assertEqual(second,first);self.assertEqual(d.count,1);self.assertEqual(d.manualStatus,'added');self.assertIn('вже',d.manualMessage.lower())
 def test_unverified_candidate_fails_closed_with_visible_error(self):
  d=module.Devices();d._manual_result={'host':'192.168.1.50','camera':True,'openipc':True,'identityVerified':False,'identity':{'verified':False},'evidence':[]};self.assertEqual(d.addDiscovered('192.168.1.50','Camera',True),'');self.assertEqual(d.count,0);self.assertEqual(d.manualStatus,'error');self.assertTrue(d.manualError)
 @patch('devices_routeaware.fingerprint')
 def test_authenticated_add_passes_secret_only_to_probe(self,probe):
  d=module.Devices();probe.return_value=self.verified();did=d.authenticateAndAdd('192.168.1.50','Camera','root','session-secret');self.assertTrue(did);self.assertEqual(probe.call_args.args[2:4],('root','session-secret'));self.assertNotIn('session-secret',repr(d.manualResult));self.assertNotIn('session-secret',repr(d.items));self.assertEqual(d.manualStatus,'added')
if __name__=='__main__':unittest.main()
