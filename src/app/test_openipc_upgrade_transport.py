import unittest
from openipc_upgrade_transport import OpenIPCUpgradeAdapter
class Devices:
 def __init__(self,verified=True):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':verified,'platform':'ssc30kq','sensor':'imx335'}}]
class Transport:
 def __init__(self,result=True):self.calls=[];self.result=result
 def run(self,host,argv):self.calls.append((host,argv));return self.result
class Tests(unittest.TestCase):
 def test_upgrade_uses_fixed_argv_and_observed_host(self):
  t=Transport();a=OpenIPCUpgradeAdapter(Devices(),t);self.assertTrue(a.execute('cam','ssc30kq-imx335','upgrade',{},{}));self.assertEqual(t.calls,[('192.168.1.50',['sysupgrade','-k','-r'])])
 def test_unverified_camera_never_reaches_transport(self):
  t=Transport();a=OpenIPCUpgradeAdapter(Devices(False),t);self.assertFalse(a.execute('cam','ssc30kq-imx335','upgrade',{},{}));self.assertEqual(t.calls,[])
 def test_adapter_rejects_non_upgrade_modes(self):
  t=Transport();a=OpenIPCUpgradeAdapter(Devices(),t);self.assertFalse(a.execute('cam','ssc30kq-imx335','recovery-fullflash',{},{}));self.assertEqual(t.calls,[])
if __name__=='__main__':unittest.main()
