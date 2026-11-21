import unittest
from post_flash_verify import verify_post_flash
class PostFlashVerifyTests(unittest.TestCase):
 def test_verified_matching_observation_passes(self):
  before={"platform":"ssc30kq","sensor":"imx335"};observed={"verified":True,"platform":"ssc30kq","sensor":"imx335","firmware":"2.5","evidence":["Majestic /api/v1/config.json"]};r=verify_post_flash(before,observed,{"platform":"ssc30kq","sensor":"imx335"},"2.5");self.assertTrue(r["ok"])
 def test_wrong_sensor_or_firmware_fails(self):
  observed={"verified":True,"platform":"ssc30kq","sensor":"imx415","firmware":"old","evidence":["Majestic /api/v1/config.json"]};r=verify_post_flash({"platform":"ssc30kq","sensor":"imx335"},observed,{"platform":"ssc30kq","sensor":"imx335"},"new");self.assertFalse(r["ok"])
 def test_missing_observation_is_unavailable(self):self.assertFalse(verify_post_flash({}, {}, {"platform":"ssc30kq","sensor":"imx335"})["ok"])
if __name__=="__main__":unittest.main()
