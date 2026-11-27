import unittest
from camera_presets import CameraPresets
from camera_preset_executor import CameraPresetExecutor
class Devices:
 def __init__(self):self.items=[{'id':'cam','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335'}}]
class Adapter:
 def __init__(self):self.calls=[]
 def execute(self,*args):self.calls.append(args);return True
class MutatingAdapter(Adapter):
 def execute(self,*args):self.calls.append(args);args[1]['settings']['orientation']='mutated';return True
class Tests(unittest.TestCase):
 def setUp(self):self.devices=Devices();self.presets=CameraPresets(self.devices);self.presets.selectForDevice('ssc30kq-imx335-fpv-v1','cam');self.presets.buildApplyPlan()
 def test_no_adapter_keeps_hardware_pending(self):
  x=CameraPresetExecutor(self.presets);self.assertFalse(x.executePrepared());self.assertEqual(x.status['state'],'hardware-validation-pending')
 def test_identity_change_after_plan_blocks_execution(self):
  x=CameraPresetExecutor(self.presets);a=Adapter();x.register_adapter(a);self.devices.items[0]['openipcIdentity']['sensor']='imx415';self.assertFalse(x.executePrepared());self.assertEqual(a.calls,[])
 def test_plan_cannot_gain_video_profile_or_unknown_setting(self):
  x=CameraPresetExecutor(self.presets);a=Adapter();x.register_adapter(a);self.presets._result['plan']['appliesVideoProfile']=True;self.assertFalse(x.executePrepared());self.assertEqual(a.calls,[]);self.presets.buildApplyPlan();self.presets._result['plan']['settings']['codec']='h265';self.assertFalse(x.executePrepared());self.assertEqual(a.calls,[])
 def test_adapter_receives_detached_camera_only_plan(self):
  before=self.presets.result['plan'];x=CameraPresetExecutor(self.presets);a=MutatingAdapter();x.register_adapter(a);self.assertTrue(x.executePrepared());self.assertEqual(self.presets.result['plan'],before);self.assertNotIn('codec',a.calls[0][1]['settings']);self.assertFalse(a.calls[0][1]['appliesVideoProfile'])
 def test_apply_requires_explicit_post_observation(self):
  x=CameraPresetExecutor(self.presets);x.register_adapter(Adapter());self.assertTrue(x.executePrepared());self.assertEqual(x.status['state'],'applied-pending-verification');self.assertTrue(x.verifyObserved(True));self.assertEqual(x.status['state'],'verified')
 def test_missing_post_observation_fails(self):
  x=CameraPresetExecutor(self.presets);x.register_adapter(Adapter());self.assertTrue(x.executePrepared());self.assertFalse(x.verifyObserved(False));self.assertEqual(x.status['state'],'error')
if __name__=='__main__':unittest.main()
