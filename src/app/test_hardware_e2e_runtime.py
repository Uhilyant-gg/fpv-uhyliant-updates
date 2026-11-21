import unittest
from hardware_e2e_runtime import HardwareE2ERuntime
class Signal:
 def __init__(self):self.handlers=[]
 def connect(self,handler):self.handlers.append(handler)
 def emit(self):
  for handler in list(self.handlers):handler()
class Obj:
 def __init__(self):self.changed=Signal()
class Diagnostics(Obj):
 def __init__(self):super().__init__();self.exports=[]
 def build(self):return {'network':{'evidence':{'summary':{'safeRoutes':1},'devices':[{'host':'192.168.1.50','reachable':True},{'host':'192.168.1.51','reachable':True}]}}}
 def exportStage(self,label):self.exports.append(label);return label+'.json'
class Credentials(Obj):
 def __init__(self):super().__init__();self.password=True
 def snapshot(self):return {'hasPassword':self.password}
class Devices(Obj):
 def __init__(self):super().__init__();self._items=[{'id':'cam','active':True,'host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['OpenIPC status.cgi']}},{'id':'cam2','active':False,'host':'192.168.1.51','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx415','firmware':'old','evidence':['OpenIPC status.cgi']}}]
class Firmware(Obj):
 def __init__(self):
  super().__init__();self.artifact={'verified':True,'sha256':'a'*64,'size':100,'build':'new'};self.executionPlan={'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':'approval','artifactSha256':'a'*64,'artifactSize':100};self.result={'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':'approval','artifactSha256':'a'*64}
class Tests(unittest.TestCase):
 def make(self):
  devices=Devices();diagnostics=Diagnostics();credentials=Credentials();firmware=Firmware();return HardwareE2ERuntime(devices,diagnostics,credentials,firmware),devices,diagnostics,credentials,firmware
 def test_host_key_is_bound_to_complete_ready_transaction(self):
  r,_,_,_,_=self.make();self.assertFalse(r.readiness['ready']);r.setHostKeyAccepted(True);self.assertTrue(r.readiness['ready'])
 def test_preflight_export_uses_staged_diagnostics_boundary(self):
  r,_,diagnostics,_,_=self.make();self.assertEqual(r.exportPreflight(),'hardware-e2e-preflight.json');self.assertEqual(diagnostics.exports,['hardware-e2e-preflight']);self.assertEqual(r.captures['preflight'],'hardware-e2e-preflight.json')
 def test_all_e2e_capture_stages_are_distinct(self):
  r,_,diagnostics,_,_=self.make();self.assertEqual(r.capture('post-update'),'hardware-e2e-post-update.json');self.assertEqual(r.capture('failure'),'hardware-e2e-failure.json');self.assertEqual(diagnostics.exports,['hardware-e2e-post-update','hardware-e2e-failure']);self.assertEqual(r.capture('other'),'')
 def test_identity_change_revokes_host_key_confirmation(self):
  r,devices,_,_,_=self.make();r.setHostKeyAccepted(True);devices._items[0]['openipcIdentity']['sensor']='imx415';devices.changed.emit();self.assertFalse(r.hostKeyAccepted)
 def test_artifact_plan_or_approval_change_revokes_host_key_confirmation(self):
  for mutate in (lambda f:f.artifact.__setitem__('sha256','b'*64),lambda f:f.executionPlan.__setitem__('approvalToken','changed'),lambda f:f.result.__setitem__('approvalToken','changed')):
   r,_,_,_,firmware=self.make();r.setHostKeyAccepted(True);mutate(firmware);firmware.changed.emit();self.assertFalse(r.hostKeyAccepted);self.assertFalse(r.readiness['ready'])
 def test_explicit_selection_must_match_transaction_device(self):
  r,_,_,_,firmware=self.make();firmware.executionPlan['deviceId']='cam2';firmware.result['deviceId']='cam2';r.selectDevice('cam2');r.setHostKeyAccepted(True);self.assertTrue(r.readiness['ready']);r.selectDevice('cam');self.assertFalse(r.readiness['ready'])
 def test_unknown_explicit_selection_fails_closed(self):
  r,_,_,_,_=self.make();r.selectDevice('missing');self.assertFalse(r.readiness['ready']);self.assertIsNone(r.readiness['host'])
if __name__=='__main__':unittest.main()
