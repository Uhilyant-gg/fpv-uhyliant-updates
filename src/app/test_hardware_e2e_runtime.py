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
 def build(self):return {'network':{'evidence':{'summary':{'safeRoutes':1},'devices':[{'host':'192.168.1.50','reachable':True}]}}}
 def exportStage(self,label):self.exports.append(label);return label+'.json'
class Credentials(Obj):
 def __init__(self):super().__init__();self.password=True
 def snapshot(self):return {'hasPassword':self.password}
class Devices(Obj):
 def __init__(self):super().__init__();self._items=[{'id':'cam','active':True,'host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['OpenIPC status.cgi']}}]
class Firmware(Obj):
 def __init__(self):super().__init__();self.artifact={'verified':True,'sha256':'a'*64,'size':100,'build':'new'};self.executionPlan={'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':'approval','artifactSha256':'a'*64,'artifactSize':100};self.result={'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':'approval','artifactSha256':'a'*64}
class Session(Obj):
 def __init__(self):super().__init__();self.result={'state':'ready','observedFirmware':'','verification':{}}
class Tests(unittest.TestCase):
 def make(self):
  d=Devices();diag=Diagnostics();cred=Credentials();fw=Firmware();session=Session();runtime=HardwareE2ERuntime(d,diag,cred,fw,session);return runtime,diag,session
 def ready(self,r):r.setHostKeyAccepted(True);self.assertTrue(r.readiness['ready'])
 def test_preflight_capture_requires_complete_readiness(self):
  r,diag,_=self.make();self.assertEqual(r.capture('preflight'),'');self.ready(r);self.assertEqual(r.capture('preflight'),'hardware-e2e-preflight.json');self.assertEqual(diag.exports,['hardware-e2e-preflight'])
 def test_post_update_capture_requires_verified_observed_firmware(self):
  r,diag,s=self.make();self.ready(r);self.assertEqual(r.capture('post-update'),'');s.result={'state':'verified','observedFirmware':'new','verification':{'ok':True,'identity':{'firmware':'new'}}};s.changed.emit();self.assertEqual(r.capture('post-update'),'hardware-e2e-post-update.json');self.assertEqual(diag.exports,['hardware-e2e-post-update'])
 def test_verified_without_observed_firmware_cannot_capture_success(self):
  r,diag,s=self.make();self.ready(r);s.result={'state':'verified','observedFirmware':'','verification':{'ok':True,'identity':{}}};s.changed.emit();self.assertFalse(r.evidenceReadiness['postUpdate']);self.assertEqual(r.capture('post-update'),'');self.assertEqual(diag.exports,[])
 def test_failure_capture_requires_terminal_failure(self):
  r,diag,s=self.make();self.ready(r);self.assertEqual(r.capture('failure'),'');s.result={'state':'error','observedFirmware':'','verification':{}};s.changed.emit();self.assertEqual(r.capture('failure'),'hardware-e2e-failure.json');self.assertEqual(diag.exports,['hardware-e2e-failure'])
 def test_blocked_is_captureable_failure_but_reboot_pending_is_not(self):
  r,_,s=self.make();self.ready(r);s.result={'state':'reboot-pending','observedFirmware':'','verification':{}};s.changed.emit();self.assertFalse(r.evidenceReadiness['failure']);s.result={'state':'blocked','observedFirmware':'','verification':{}};s.changed.emit();self.assertTrue(r.evidenceReadiness['failure'])
if __name__=='__main__':unittest.main()
