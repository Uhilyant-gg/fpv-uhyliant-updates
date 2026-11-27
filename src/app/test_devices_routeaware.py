import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QObject,Signal
import devices as devices_module
import devices_routeaware as module

class ErrorState(QObject):
 discoveryChanged=Signal();manualChanged=Signal()
 def __init__(self):
  super().__init__();self._items=[];self._discovered=[];self._scanning=True;self._worker=object();self._stage="";self._status="";self._pd=0;self._pt=0;self._found=0;self._manual_busy=True;self._manual_result={};self._manual_error="";self._manual_status="checking";self._manual_message="";self._manual_worker=object();self._manual_requested_host="192.168.1.50"
 def _remember_host(self,*args):pass
 def _set_manual(self,*args):module.Devices._set_manual(self,*args)
 @property
 def manualError(self):return self._manual_error
 @property
 def scanStatus(self):return self._status

class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);devices_module.DATA=root;devices_module.DB=root/'devices.sqlite3';self.orig=devices_module.interfaces;devices_module.interfaces=lambda:[]
 def tearDown(self):devices_module.interfaces=self.orig;self.temp.cleanup()
 def verified(self):return {'host':'192.168.1.50','camera':True,'openipc':True,'identityVerified':True,'identity':{'verified':True,'platform':'ssc30kq','soc':'ssc338q','sensor':'imx335','firmware':'v1','majestic':'','evidence':['observed']},'evidence':['observed'],'streams':[]}
 def test_known_hosts_include_saved_and_last_seen(self):
  d=module.Devices();d.addDevice('Camera','OpenIPC','192.168.1.40',80,'Network','');d._remember_host('192.168.1.50',True);self.assertIn('192.168.1.40',d._known_hosts());self.assertIn('192.168.1.50',d._known_hosts())
 def test_discovery_properties_have_safe_qt_notify_metadata(self):
  with patch.object(module.LegacyDevices,'_init',lambda self:None),patch.object(module.LegacyDevices,'_load',lambda self:None),patch.object(module.Devices,'_init_discovery_history',lambda self:None):d=module.Devices()
  meta=module.Devices.staticMetaObject;properties=[meta.property(i) for i in range(meta.propertyCount())]
  for prop in properties:
   self.assertTrue(prop.name() and prop.typeName())
   if prop.hasNotifySignal():self.assertTrue(prop.notifySignal().methodSignature())
  d._stage='Пошук камер';d._pd=1;d._pt=2;d._found=0
  notifications=[];d.scanStateChanged.connect(lambda:notifications.append(True));d.discoveryChanged.emit()
  self.assertEqual(d.scanStage,'Пошук камер');self.assertEqual(d.scanDone,1);self.assertEqual(notifications,[True])
 def test_manual_completion_clears_busy_and_exposes_verified_state(self):
  d=module.Devices();d._manual_busy=True;d._manual_requested_host='192.168.1.50';d._on_manual_done(self.verified(),'');self.assertFalse(d.manualBusy);self.assertEqual(d.manualStatus,'verified');self.assertEqual(d.manualMessage,'OpenIPC підтверджено');self.assertEqual(d.manualResult['identity']['sensor'],'imx335')
 def test_successful_manual_observation_updates_only_matching_saved_device(self):
  d=module.Devices();d.addDevice('Camera','OpenIPC','192.168.1.50',80,'Network','');d._manual_busy=True;d._manual_requested_host='192.168.1.50'
  d._on_manual_done(self.verified(),'')
  self.assertGreater(d.items[0]['lastObservedAt'],0)
 def test_manual_auth_candidate_has_explicit_state(self):
  d=module.Devices();d._manual_busy=True;d._manual_requested_host='192.168.1.50';d._on_manual_done({'host':'192.168.1.50','camera':True,'openipc':False,'identityVerified':False,'authRequired':True},'');self.assertFalse(d.manualBusy);self.assertEqual(d.manualStatus,'auth-required');self.assertIn('логін',d.manualMessage)
 def test_manual_no_camera_has_visible_error_state(self):
  d=module.Devices();d._manual_busy=True;d._manual_requested_host='192.168.1.50';d._on_manual_done({},'');self.assertFalse(d.manualBusy);self.assertEqual(d.manualStatus,'error');self.assertTrue(d.manualError)
 def test_manual_probe_exception_shows_recovery_guidance_not_raw_error(self):
  d=ErrorState();module.Devices._on_manual_done(d,{},'Connection refused: socket error')
  self.assertIn('Перевірте',d.manualError);self.assertNotIn('Connection refused',d.manualError);self.assertNotIn('socket error',d.manualError)
 def test_discovery_exception_shows_recovery_guidance_not_raw_error(self):
  d=ErrorState();module.Devices._on_done(d,[],False,'Unknown exception: timeout')
  self.assertIn('Перевірте мережу',d.scanStatus);self.assertNotIn('Unknown exception',d.scanStatus);self.assertNotIn('timeout',d.scanStatus)
 def test_manual_result_for_unrequested_host_fails_closed(self):
  d=module.Devices();d._manual_busy=True;d._manual_requested_host='192.168.1.40';d._on_manual_done(self.verified(),'');self.assertFalse(d.manualBusy);self.assertEqual(d.manualStatus,'error');self.assertEqual(d.manualResult,{});self.assertIn('поточній адресі',d.manualError)
 def test_verified_manual_candidate_is_staged_until_video_is_verified(self):
  d=module.Devices();d._manual_result=self.verified();did=d.addDiscovered('192.168.1.50','Camera',True);self.assertTrue(did);self.assertEqual(d.count,1);self.assertEqual(d.manualStatus,'staged');saved=d.items[0];self.assertTrue(saved['openipcIdentity']['verified']);self.assertEqual(saved['openipcIdentity']['sensor'],'imx335');self.assertEqual(saved['onboardingState'],'pending-video');self.assertEqual(d.homeItems,[])
 def test_scan_automatically_stages_supported_camera_without_showing_it_on_home(self):
  d=module.Devices();d._on_done([self.verified()],False,'')
  self.assertEqual(d.count,1);self.assertEqual(d.items[0]['onboardingState'],'pending-video');self.assertEqual(d.homeItems,[])
 def test_missing_firmware_opens_the_guarded_firmware_step(self):
  d=module.Devices();candidate=self.verified();candidate['identity']['firmware']='';requested=[];d.firmwarePreparationRequested.connect(requested.append);d._on_done([candidate],False,'')
  self.assertEqual(d.items[0]['onboardingState'],'pending-firmware');self.assertEqual(requested,[d.items[0]['id']])
 def test_scan_automatically_adds_only_camera_with_verified_video(self):
  d=module.Devices();candidate=self.verified();candidate['streams']=[{'name':'Основний','port':554,'path':'/','protocol':'rtsp'}];d._on_done([candidate],False,'')
  self.assertEqual(len(d.homeItems),1);self.assertEqual(d.homeItems[0]['onboardingState'],'ready');self.assertEqual(len(d.streams),1)
 def test_scan_does_not_stage_unsupported_sensor(self):
  d=module.Devices();candidate=self.verified();candidate['identity']['sensor']='unknown';d._on_done([candidate],False,'')
  self.assertEqual(d.count,0)
 def test_discovery_does_not_overwrite_an_unrelated_device_at_same_host(self):
  d=module.Devices();d.addDevice('Controller','Controller','192.168.1.50',80,'Network','');d._on_done([self.verified()],False,'')
  self.assertEqual(d.count,2);self.assertTrue(any(device['name']=='Controller' and device['type']=='Controller' for device in d.items));self.assertTrue(any(device['type']=='OpenIPC' for device in d.items))
 def test_verified_firmware_and_rtsp_stream_complete_onboarding(self):
  d=module.Devices();d._manual_result=self.verified();did=d.addDiscovered('192.168.1.50','Camera',True)
  verification={'ok':True,'identity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new','evidence':['OpenIPC status.cgi']},'rediscoveredHost':'192.168.1.60','streams':[]}
  self.assertTrue(d.completeFirmwareOnboarding(did,verification));self.assertEqual(d.items[0]['onboardingState'],'pending-video');self.assertEqual(d.homeItems,[])
  verification['streams']=[{'name':'Основний','port':554,'path':'/','protocol':'rtsp'}]
  self.assertTrue(d.completeFirmwareOnboarding(did,verification));self.assertEqual(d.homeItems[0]['host'],'192.168.1.60');self.assertEqual(d.homeItems[0]['onboardingState'],'ready');self.assertEqual(len(d.streams),1)
 def test_device_update_emits_change_event_only_for_existing_device(self):
  d=module.Devices();did=d.addDevice('Camera','OpenIPC','192.168.1.40',80,'Network','');d.markObserved('192.168.1.40');events=[];d.deviceUpdated.connect(lambda:events.append(True))
  self.assertTrue(d.updateDevice(did,'Updated camera','192.168.1.41',8080,'Updated notes'));self.assertEqual(events,[True]);self.assertEqual(d.items[0]['name'],'Updated camera');self.assertEqual(d.items[0]['lastObservedAt'],0)
  self.assertFalse(d.updateDevice('missing','Unknown','192.168.1.42',80,''));self.assertEqual(events,[True])
 def test_duplicate_add_is_idempotent_and_visible(self):
  d=module.Devices();d._manual_result=self.verified();first=d.addDiscovered('192.168.1.50','Camera',True);second=d.addDiscovered('192.168.1.50','Camera',True);self.assertEqual(second,first);self.assertEqual(d.count,1);self.assertEqual(d.manualStatus,'staged')
 def test_unverified_candidate_fails_closed_with_visible_error(self):
  d=module.Devices();d._manual_result={'host':'192.168.1.50','camera':True,'openipc':True,'identityVerified':False,'identity':{'verified':False},'evidence':[]};self.assertEqual(d.addDiscovered('192.168.1.50','Camera',True),'');self.assertEqual(d.count,0);self.assertEqual(d.manualStatus,'error');self.assertTrue(d.manualError)
 @patch('devices_routeaware.fingerprint')
 def test_authenticated_add_passes_secret_only_to_probe(self,probe):
  d=module.Devices();probe.return_value=self.verified();did=d.authenticateAndAdd('192.168.1.50','Camera','root','session-secret');self.assertTrue(did);self.assertEqual(probe.call_args.args[2:4],('root','session-secret'));self.assertNotIn('session-secret',repr(d.manualResult));self.assertNotIn('session-secret',repr(d.items));self.assertEqual(d.manualStatus,'staged')
if __name__=='__main__':unittest.main()
