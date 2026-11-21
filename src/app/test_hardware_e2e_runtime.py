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
 def __init__(self):super().__init__()
 def build(self):return {'network':{'evidence':{'summary':{'safeRoutes':1},'devices':[{'host':'192.168.1.50','reachable':True}]}}}
 def export(self):return 'bundle.json'
class Credentials(Obj):
 def __init__(self):super().__init__();self.password=True
 def snapshot(self):return {'hasPassword':self.password}
class Devices(Obj):
 def __init__(self):
  super().__init__();self._items=[{'id':'cam','active':True,'host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['OpenIPC status.cgi']}}]
class Tests(unittest.TestCase):
 def make(self):
  devices=Devices();diagnostics=Diagnostics();credentials=Credentials();return HardwareE2ERuntime(devices,diagnostics,credentials),devices,diagnostics,credentials
 def test_host_key_is_explicit_last_gate(self):
  r,_,_,_=self.make();self.assertFalse(r.readiness['ready']);self.assertIn('hostKeyAccepted',r.readiness['missing']);r.setHostKeyAccepted(True);self.assertTrue(r.readiness['ready'])
 def test_preflight_export_uses_sanitized_diagnostics_boundary(self):
  r,_,_,_=self.make();self.assertEqual(r.exportPreflight(),'bundle.json')
 def test_host_key_confirmation_is_bound_to_selected_device_identity(self):
  r,devices,_,_=self.make();r.setHostKeyAccepted(True);self.assertTrue(r.hostKeyAccepted);devices._items[0]['host']='192.168.1.51';devices.changed.emit();self.assertFalse(r.hostKeyAccepted);self.assertFalse(r.readiness['ready'])
 def test_platform_or_sensor_change_invalidates_confirmation(self):
  r,devices,_,_=self.make();r.setHostKeyAccepted(True);devices._items[0]['openipcIdentity']['sensor']='imx415';devices.changed.emit();self.assertFalse(r.hostKeyAccepted);self.assertIn('hostKeyAccepted',r.readiness['missing'])
if __name__=='__main__':unittest.main()
