import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
class Devices:
 def __init__(self):self.items=[{'id':'cam','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]
class Adapter:
 def __init__(self):self.calls=[]
 def execute(self,*args):self.calls.append(args);return True
class ExecutorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/'fw.bin';self.image.write_bytes(b'safe-test');sha=hashlib.sha256(self.image.read_bytes()).hexdigest();self.devices=Devices();self.center=FirmwareCenter(self.devices);self.center.verifyImage(str(self.image),sha);self.center.precheck('cam','ssc30kq-imx335','upgrade',True,True);self.center.prepareExecution('cam','ssc30kq-imx335','upgrade')
 def tearDown(self):self.tmp.cleanup()
 def test_no_adapter_means_no_destructive_execution(self):
  x=FirmwareExecutor(self.center);self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(x.status['state'],'hardware-validation-pending')
 def test_artifact_change_blocks_executor_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.image.write_bytes(b'changed');self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_identity_change_after_approval_blocks_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.devices.items[0]['openipcIdentity']['sensor']='imx415';self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[]);self.assertEqual(x.status['state'],'blocked')
 def test_identity_verification_loss_after_approval_blocks_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.devices.items[0]['openipcIdentity']['verified']=False;self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_device_removal_after_approval_blocks_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.devices.items.clear();self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_adapter_receives_snapshot_not_live_plan_objects(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));artifact=a.calls[0][3];plan=a.calls[0][4];self.center.artifact['sha256']='mutated-after-handoff';self.assertNotEqual(artifact['sha256'],self.center.artifact['sha256']);self.assertEqual(plan['deviceId'],'cam')
 def test_observed_post_flash_identity_completes_lifecycle(self):
  x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));observed={'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new','evidence':['Majestic /api/v1/config.json']};self.assertTrue(x.verifyObserved(observed,'new'));self.assertEqual(x.status['state'],'verified');self.assertTrue(x.status['verification']['ok'])
 def test_wrong_observed_firmware_fails_verification(self):
  x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));observed={'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']};self.assertFalse(x.verifyObserved(observed,'new'));self.assertEqual(x.status['state'],'error')
if __name__=='__main__':unittest.main()
