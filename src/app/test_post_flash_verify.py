import unittest
from post_flash_verify import verify_post_flash
class PostFlashVerifyTests(unittest.TestCase):
 def setUp(self):self.before={'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old'};self.profile={'platform':'ssc30kq','sensor':'imx335'}
 def test_missing_observation_is_unavailable(self):self.assertFalse(verify_post_flash(self.before,{},self.profile)['ok'])
 def test_verified_matching_observation_passes(self):
  observed={'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new','evidence':['Majestic /api/v1/config.json']};self.assertTrue(verify_post_flash(self.before,observed,self.profile)['ok'])
 def test_wrong_sensor_or_firmware_fails(self):
  observed={'verified':True,'platform':'ssc30kq','sensor':'imx415','firmware':'old','evidence':['Majestic /api/v1/config.json']};self.assertFalse(verify_post_flash(self.before,observed,self.profile,'new')['ok'])
 def test_online_upgrade_accepts_new_observed_version_without_inventing_expected_version(self):
  observed={'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'observed-after-upgrade','evidence':['OpenIPC status.cgi']};r=verify_post_flash(self.before,observed,self.profile,'');self.assertTrue(r['ok']);self.assertEqual(r['identity']['firmware'],'observed-after-upgrade')
if __name__=='__main__':unittest.main()
