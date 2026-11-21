import unittest
from camera_presets import CameraPresets
class Devices:
 def __init__(self,identity):self.items=[{"id":"cam","openipcIdentity":identity}]
class CameraPresetTests(unittest.TestCase):
 def test_preset_matches_verified_hardware_fields_without_video_profile(self):
  p=CameraPresets(Devices({"platform":"ssc30kq","sensor":"imx335"}));self.assertTrue(p.selectForDevice("ssc30kq-imx335-fpv-v1","cam"));self.assertTrue(p.belongsToFirmware("ssc30kq-imx335-fpv-v1"));self.assertFalse(p.result["preset"]["settings"]["applyVideoProfile"])
 def test_wrong_sensor_is_rejected(self):
  p=CameraPresets(Devices({"platform":"ssc30kq","sensor":"imx415"}));self.assertFalse(p.selectForDevice("ssc30kq-imx335-fpv-v1","cam"))
if __name__=="__main__":unittest.main()
