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
 def __init__(self):self.items=[{'id':'cam','name':'Camera','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old'}}]

class Tests(unittest.TestCase):
 def setUp(self):
  self.data=b'firmware';self.sha=hashlib.sha256(self.data).hexdigest();self.devices=Devices();self.center=FirmwareCenter(self.devices);self.executor=FirmwareExecutor(self.center);self.session=FirmwareUpdateSession(self.executor,self.devices,sleep=lambda _:None,rediscovery_attempts=1,rediscovery_interval=0)
  self.entry={'platform':'ssc30kq','sensor':'imx335','variant':'lite','channel':'nightly','build':'b1','url':FIXTURE_URL,'sha256':self.sha,'size':len(self.data)}
 def acquisition(self,td):
  service=OpenIPCFirmwareAcquisition(self.center,td,opener=lambda *a,**k:Response(self.data));service._catalog=[dict(self.entry)];service._generation=1;return service
 def test_official_download_flows_into_immutable_execution_plan(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   acquisition=self.acquisition(td);self.assertTrue(acquisition.selectForDevice('cam','nightly','b1','lite')['ready']);self.assertTrue(acquisition.downloadSelected('cam'));self.assertTrue(self.center.artifact['verified']);self.assertEqual(self.center.artifact['sha256'],self.sha)
   self.assertTrue(self.center.precheck('cam','ssc30kq-imx335','upgrade',True,True));self.assertTrue(self.center.prepareExecution('cam','ssc30kq-imx335','upgrade'));plan=self.center.executionPlan;self.assertTrue(plan['ready']);self.assertEqual(plan['artifactSha256'],self.sha);self.assertEqual(plan['artifactSize'],len(self.data))
   self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.session.result['state'],'hardware-validation-pending');self.assertFalse(self.executor.busy)
 def test_device_identity_change_invalidates_approved_execution(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   acquisition=self.acquisition(td);acquisition.selectForDevice('cam','nightly','b1','lite');self.assertTrue(acquisition.downloadSelected('cam'));self.assertTrue(self.center.precheck('cam','ssc30kq-imx335','upgrade',True,True));self.assertTrue(self.center.prepareExecution('cam','ssc30kq-imx335','upgrade'))
   self.devices.items[0]['host']='192.168.1.99';self.assertFalse(self.center.approvalMatches('cam','ssc30kq-imx335','upgrade'));self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.executor.status['state'],'blocked');self.assertFalse(self.executor.busy)
 def test_tampered_downloaded_image_is_blocked_before_transport(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   acquisition=self.acquisition(td);acquisition.selectForDevice('cam','nightly','b1','lite');self.assertTrue(acquisition.downloadSelected('cam'));self.assertTrue(self.center.precheck('cam','ssc30kq-imx335','upgrade',True,True));self.assertTrue(self.center.prepareExecution('cam','ssc30kq-imx335','upgrade'));Path(self.center.artifact['path']).write_bytes(b'tampered')
   self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.executor.status['state'],'blocked');self.assertFalse(self.executor.busy)

if __name__=='__main__':unittest.main()
