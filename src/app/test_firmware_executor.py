import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
class Devices:
 def __init__(self):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]
class Adapter:
 def __init__(self,result=True):self.calls=[];self.result=result
 def execute(self,*args):self.calls.append(args);return self.result
class ExecutorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/'fw.bin';self.image.write_bytes(b'safe-test');sha=hashlib.sha256(self.image.read_bytes()).hexdigest();self.devices=Devices();self.center=FirmwareCenter(self.devices);self.center.verifyImage(str(self.image),sha);self.center.precheck('cam','ssc30kq-imx335','upgrade',False,False);self.center.prepareExecution('cam','ssc30kq-imx335','upgrade')
 def tearDown(self):self.tmp.cleanup()
 def test_no_adapter_means_no_destructive_execution(self):x=FirmwareExecutor(self.center);self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(x.status['state'],'hardware-validation-pending')
 def test_artifact_change_blocks_executor_handoff(self):x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.image.write_bytes(b'changed');self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_identity_change_after_approval_blocks_handoff(self):x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.devices.items[0]['openipcIdentity']['sensor']='imx415';self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_verification_context_preserves_unknown_target_for_manual_artifact(self):x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));c=x.verificationContext();self.assertEqual(c['host'],'192.168.1.50');self.assertEqual(c['expectedFirmware'],'')
 def test_verification_context_binds_catalog_build_when_available(self):
  self.center._artifact['build']='2026.11.21';x=FirmwareExecutor(self.center);self.center._result['approvalToken']=self.center._approval_token('cam','ssc30kq-imx335','upgrade',self.devices.items[0],self.devices.items[0]['openipcIdentity']);self.center._plan['approvalToken']=self.center._result['approvalToken'];x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(x.verificationContext()['expectedFirmware'],'2026.11.21')
 def test_lock_remains_until_terminal_verification(self):
  x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));context,nonce=x.beginRediscovery();self.assertTrue(context['ready']);self.assertTrue(x.busy);self.assertTrue(x.acceptRediscoveredVerification({'rediscovered':True},{'ok':True,'identity':{'firmware':'new'}},nonce));self.assertFalse(x.busy);self.assertEqual(x.status['state'],'verified')
 def test_missing_observed_firmware_fails_terminal_verification(self):
  x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));_,nonce=x.beginRediscovery();self.assertFalse(x.acceptRediscoveredVerification({'rediscovered':True},{'ok':True,'identity':{}},nonce));self.assertEqual(x.status['state'],'error');self.assertFalse(x.status['verification']['ok']);self.assertFalse(x.busy)
if __name__=='__main__':unittest.main()
