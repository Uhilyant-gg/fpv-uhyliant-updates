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
 def export(self):return 'bundle.json'
 def exportStage(self,label):self.exports.append(label);return label+'.json'
class Credentials(Obj):
 def __init__(self):super().__init__();self.password=True
 def snapshot(self):return {'hasPassword':self.password}
class Devices(Obj):
 def __init__(self):super().__init__();self._items=[{'id':'cam','active':True,'host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['OpenIPC status.cgi']}},{'id':'cam2','active':False,'host':'192.168.1.51','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx415','firmware':'old','evidence':['OpenIPC status.cgi']}}]
class Firmware(Obj):
 def __init__(self):super().__init__();self.artifact={'verified':True,'sha256':'a'*64,'size':100,'build':'new'};self.executionPlan={'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':'approval'}
class Tests(unittest.TestCase):
 def make(self):
  devices=Devices();diagnostics=Diagnostics();credentials=Credentials();firmware=Firmware();return HardwareE2ERuntime(devices,diagnostics,credentials,firmware),devices,diagnostics,credentials,firmware
 def test_host_key_is_explicit_last_gate(self):
  r,_,_,_,_=self.make();self.assertFalse(r.readiness['ready']);self.assertIn('hostKeyAccepted',r.readiness['missing']);r.setHostKeyAccepted(True);self.assertTrue(r.readiness['ready'])
 def test_preflight_export_uses_sanitized_staged_diagnostics_boundary(self):
  r,_,diagnostics,_,_=self.make();self.assertEqual(r.exportPreflight(),'hardware-e2e-preflight.json');self.assertEqual(diagnostics.exports,['hardware-e2e-preflight']);self.assertEqual(r.captures['preflight'],'hardware-e2e-preflight.json')
 def test_all_e2e_capture_stages_use_staged_diagnostics_boundary(self):
  r,_,diagnostics,_,_=self.make();self.assertEqual(r.capture('post-update'),'hardware-e2e-post-update.json');self.assertEqual(r.capture('failure'),'hardware-e2e-failure.json');self.assertEqual(diagnostics.exports,['hardware-e2e-post-update','hardware-e2e-failure']);self.assertEqual(r.capture('other'),'')
 def test_host_key_confirmation_is_bound_to_selected_device_identity(self):
  r,devices,_,_,_=self.make();r.setHostKeyAccepted(True);self.assertTrue(r.hostKeyAccepted);devices._items[0]['host']='192.168.1.51';devices.changed.emit();self.assertFalse(r.hostKeyAccepted);self.assertFalse(r.readiness['ready'])
 def test_platform_or_sensor_change_invalidates_confirmation(self):
  r,devices,_,_,_=self.make();r.setHostKeyAccepted(True);devices._items[0]['openipcIdentity']['sensor']='imx415';devices.changed.emit();self.assertFalse(r.hostKeyAccepted);self.assertIn('hostKeyAccepted',r.readiness['missing'])
 def test_explicit_firmware_selection_binds_preflight_to_same_device(self):
  r,_,_,_,firmware=self.make();firmware.executionPlan['deviceId']='cam2';r.selectDevice('cam2');self.assertEqual(r.readiness['host'],'192.168.1.51');r.setHostKeyAccepted(True);self.assertTrue(r.readiness['ready'])
 def test_changing_firmware_selection_revokes_host_key_confirmation(self):
  r,_,_,_,firmware=self.make();r.setHostKeyAccepted(True);self.assertTrue(r.hostKeyAccepted);firmware.artifact['sha256']='b'*64;firmware.changed.emit();self.assertFalse(r.hostKeyAccepted);self.assertFalse(r.readiness['ready'])
 def test_execution_plan_change_revokes_host_key_confirmation(self):
  r,_,_,_,firmware=self.make();r.setHostKeyAccepted(True);firmware.executionPlan['approvalToken']='changed';firmware.changed.emit();self.assertFalse(r.hostKeyAccepted)
 def test_unknown_explicit_selection_fails_closed(self):
  r,_,_,_,_=self.make();r.selectDevice('missing');self.assertFalse(r.readiness['ready']);self.assertIsNone(r.readiness['host'])
if __name__=='__main__':unittest.main()
