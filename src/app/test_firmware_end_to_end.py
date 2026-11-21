import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
from firmware_update_session import FirmwareUpdateSession
from openipc_firmware_acquisition import OpenIPCFirmwareAcquisition

FIXTURE_URL=''.join(('https://','fixture.invalid','/artifact'))

class Response:
 def __init__(self,data):self.data=data;self.headers={'Content-Length':str(len(data))}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def geturl(self):return FIXTURE_URL
 def read(self,limit):return self.data[:limit]

class Devices:
 def __init__(self):self.items=[{'id':'cam','name':'Camera','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]

class Transport:
 def __init__(self):self.calls=[]
 def authenticate(self,host):self.calls.append(('auth',host));return True
 def run(self,host,argv):self.calls.append(('run',host,list(argv)));return True

class Tests(unittest.TestCase):
 def setUp(self):
  self.data=b'firmware';self.sha=hashlib.sha256(self.data).hexdigest();self.devices=Devices();self.center=FirmwareCenter(self.devices);self.executor=FirmwareExecutor(self.center);self.session=FirmwareUpdateSession(self.executor,self.devices,sleep=lambda _:None,rediscovery_attempts=1,rediscovery_interval=0)
  self.entry={'platform':'ssc30kq','sensor':'imx335','variant':'lite','channel':'nightly','build':'b1','url':FIXTURE_URL,'sha256':self.sha,'size':len(self.data)}
 def acquisition(self,td):
  service=OpenIPCFirmwareAcquisition(self.center,td,opener=lambda *a,**k:Response(self.data));service._catalog=[dict(self.entry)];service._generation=1;return service
 def prepare(self,td):
  acquisition=self.acquisition(td);self.assertTrue(acquisition.selectForDevice('cam','nightly','b1','lite')['ready']);self.assertTrue(acquisition.downloadSelected('cam'));self.assertTrue(self.center.precheck('cam','ssc30kq-imx335','upgrade',True,True));self.assertTrue(self.center.prepareExecution('cam','ssc30kq-imx335','upgrade'));return acquisition
 def test_official_download_flows_into_immutable_execution_plan(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   self.prepare(td);self.assertTrue(self.center.artifact['verified']);self.assertEqual(self.center.artifact['sha256'],self.sha);plan=self.center.executionPlan;self.assertTrue(plan['ready']);self.assertEqual(plan['artifactSha256'],self.sha);self.assertEqual(plan['artifactSize'],len(self.data));self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.session.result['state'],'hardware-validation-pending');self.assertFalse(self.executor.busy)
 def test_complete_upgrade_reaches_verified_only_after_fresh_post_reboot_identity(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   self.prepare(td);transport=Transport();self.session._probe_provider=lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']};self.session._candidate_provider=lambda host:[];self.assertTrue(self.session.configure_transport(transport));self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.session.result['state'],'reboot-pending');self.assertTrue(self.executor.busy);self.assertTrue(self.session.verifyAfterReboot());self.assertEqual(self.session.result['state'],'verified');self.assertEqual(self.session.result['observedFirmware'],'new');self.assertFalse(self.executor.busy);self.assertEqual(transport.calls,[('auth','192.168.1.50'),('run','192.168.1.50',['sysupgrade','-k','-r'])])
 def test_post_reboot_missing_firmware_fails_closed(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   self.prepare(td);self.session._probe_provider=lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335'},'evidence':['OpenIPC status.cgi']};self.session._candidate_provider=lambda host:[];self.assertTrue(self.session.configure_transport(Transport()));self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertFalse(self.session.verifyAfterReboot());self.assertEqual(self.session.result['state'],'error');self.assertEqual(self.session.result['observedFirmware'],'');self.assertFalse(self.executor.busy)
 def test_rediscovery_result_with_invalid_host_fails_closed(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   self.prepare(td);self.assertTrue(self.session.configure_transport(Transport()));self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'))
   fake={'rediscovered':True,'attempts':1,'host':'','identity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new'}}
   with patch('firmware_update_session.FirmwareRediscovery.wait',return_value=fake):self.assertFalse(self.session.verifyAfterReboot())
   self.assertEqual(self.session.result['state'],'error');self.assertEqual(self.session.result['verification'],{});self.assertFalse(self.executor.busy)
 def test_device_identity_change_invalidates_approved_execution(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   self.prepare(td);self.devices.items[0]['host']='192.168.1.99';self.assertFalse(self.center.approvalMatches('cam','ssc30kq-imx335','upgrade'));self.assertFalse(self.executor.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.executor.status['state'],'blocked');self.assertFalse(self.executor.busy)
 def test_tampered_downloaded_image_is_blocked_before_transport(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   self.prepare(td);Path(self.center.artifact['path']).write_bytes(b'tampered');self.assertFalse(self.executor.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.executor.status['state'],'blocked');self.assertFalse(self.executor.busy)

if __name__=='__main__':unittest.main()
