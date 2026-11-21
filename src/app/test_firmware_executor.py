import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
class Devices:
 def __init__(self):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]
class Adapter:
 def __init__(self,result=True):self.calls=[];self.result=result
 def execute(self,*args):self.calls.append(args);return self.result
class MutatingAdapter(Adapter):
 def execute(self,*args):self.calls.append(args);args[3]['sha256']='adapter-mutated';args[4]['approvalToken']='adapter-mutated';return True
class RaisingAdapter(Adapter):
 def execute(self,*args):self.calls.append(args);raise RuntimeError('flash failed')
class ExecutorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/'fw.bin';self.image.write_bytes(b'safe-test');sha=hashlib.sha256(self.image.read_bytes()).hexdigest();self.devices=Devices();self.center=FirmwareCenter(self.devices);self.center.verifyImage(str(self.image),sha);self.center.precheck('cam','ssc30kq-imx335','upgrade',True,True);self.center.prepareExecution('cam','ssc30kq-imx335','upgrade')
 def tearDown(self):self.tmp.cleanup()
 def test_no_adapter_means_no_destructive_execution(self):
  x=FirmwareExecutor(self.center);self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(x.status['state'],'hardware-validation-pending')
 def test_artifact_change_blocks_executor_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.image.write_bytes(b'changed');self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_artifact_size_metadata_change_blocks_executor_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.center._artifact['size']+=1;self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_plan_artifact_metadata_change_blocks_executor_handoff(self):
  for key,value in (('artifactSha256','0'*64),('artifactSize',999)):
   x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.center._plan[key]=value;self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
   self.center.prepareExecution('cam','ssc30kq-imx335','upgrade')
 def test_identity_change_after_approval_blocks_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.devices.items[0]['openipcIdentity']['sensor']='imx415';self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[]);self.assertEqual(x.status['state'],'blocked')
 def test_identity_verification_loss_after_approval_blocks_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.devices.items[0]['openipcIdentity']['verified']=False;self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(a.calls,[])
 def test_adapter_receives_snapshot_not_live_plan_objects(self):
  artifact_before=self.center.artifact;plan_before=self.center.executionPlan;x=FirmwareExecutor(self.center);a=MutatingAdapter();x.register_adapter(a);self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.center.artifact,artifact_before);self.assertEqual(self.center.executionPlan,plan_before)
 def test_raw_observation_cannot_bypass_rediscovery(self):
  x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertFalse(hasattr(x,'verifyObserved'));self.assertFalse(hasattr(x,'completeVerification'));self.assertEqual(x.status['state'],'reboot-pending')
 def test_lock_remains_held_through_reboot_pending_and_blocks_repeat_execute(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertTrue(x.busy);self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(len(a.calls),1);self.assertTrue(x.busy)
 def test_reset_cannot_clear_reboot_pending_transaction(self):
  x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));x.reset();self.assertEqual(x.status['state'],'reboot-pending');self.assertTrue(x.busy);self.assertTrue(x.verificationContext()['ready'])
 def test_terminal_rediscovery_outcomes_release_lock(self):
  x=FirmwareExecutor(self.center);x.register_adapter(Adapter());self.assertTrue(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertFalse(x.failRediscovery());self.assertFalse(x.busy)
  x.reset();self.assertEqual(x.status['state'],'idle')
 def test_flash_failure_releases_lock(self):
  for adapter in (Adapter(False),RaisingAdapter()):
   x=FirmwareExecutor(self.center);x.register_adapter(adapter);self.assertFalse(x.execute('cam','ssc30kq-imx335','upgrade'));self.assertFalse(x.busy);self.assertEqual(x.status['state'],'error')
if __name__=='__main__':unittest.main()
