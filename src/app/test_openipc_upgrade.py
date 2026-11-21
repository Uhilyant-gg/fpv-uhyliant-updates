import unittest
from openipc_upgrade import upgrade_candidate,UPGRADE_ARGV
class Tests(unittest.TestCase):
 def device(self,**identity):return {'host':'192.168.1.50','openipcIdentity':identity}
 def test_verified_camera_gets_fixed_latest_sysupgrade(self):
  r=upgrade_candidate(self.device(verified=True,platform='ssc30kq',sensor='imx335',firmware='old'));self.assertTrue(r['ready']);self.assertEqual(r['argv'],list(UPGRADE_ARGV));self.assertEqual(r['currentFirmware'],'old')
 def test_unverified_openipc_is_blocked(self):self.assertFalse(upgrade_candidate(self.device(verified=False,platform='ssc30kq',sensor='imx335'))['ready'])
 def test_missing_identity_is_blocked(self):self.assertFalse(upgrade_candidate(self.device(verified=True,platform='ssc30kq',sensor=''))['ready'])
 def test_no_shell_input_from_host(self):self.assertFalse(upgrade_candidate({'host':'192.168.1.50; reboot','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335'}})['ready'])
if __name__=='__main__':unittest.main()
