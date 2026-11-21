import unittest
from hardware_e2e_runtime import HardwareE2ERuntime
class Signal:
 def connect(self,*a):pass
class Obj:changed=Signal()
class Diagnostics(Obj):
 def build(self):return {'network':{'evidence':{'summary':{'safeRoutes':1},'devices':[{'host':'192.168.1.50','reachable':True}]}}}
 def export(self):return 'bundle.json'
class Credentials(Obj):
 def snapshot(self):return {'hasPassword':True}
class Devices(Obj):
 _items=[{'id':'cam','active':True,'host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['OpenIPC status.cgi']}}]
class Tests(unittest.TestCase):
 def test_host_key_is_explicit_last_gate(self):
  r=HardwareE2ERuntime(Devices(),Diagnostics(),Credentials());self.assertFalse(r.readiness['ready']);self.assertIn('hostKeyAccepted',r.readiness['missing']);r.setHostKeyAccepted(True);self.assertTrue(r.readiness['ready'])
 def test_preflight_export_uses_sanitized_diagnostics_boundary(self):self.assertEqual(HardwareE2ERuntime(Devices(),Diagnostics(),Credentials()).exportPreflight(),'bundle.json')
if __name__=='__main__':unittest.main()
