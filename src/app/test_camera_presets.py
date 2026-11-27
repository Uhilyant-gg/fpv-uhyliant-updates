import unittest
from camera_presets import CameraPresets


class Devices:
    def __init__(self, identity):
        self.items = [{"id": "cam", "openipcIdentity": identity}]


class CameraPresetTests(unittest.TestCase):
    def test_preset_requires_verified_hardware_identity(self):
        p = CameraPresets(Devices({"verified": True, "platform": "ssc30kq", "sensor": "imx335"}))
        self.assertTrue(p.selectForDevice("ssc30kq-imx335-fpv-v1", "cam"))
        self.assertFalse(p.belongsToFirmware("ssc30kq-imx335-fpv-v1"))
        self.assertFalse(p.affectsVideoProfile("ssc30kq-imx335-fpv-v1"))
        self.assertFalse(p.result["preset"]["settings"]["applyVideoProfile"])

    def test_unverified_matching_fields_are_rejected(self):
        p = CameraPresets(Devices({"verified": False, "platform": "ssc30kq", "sensor": "imx335"}))
        self.assertFalse(p.selectForDevice("ssc30kq-imx335-fpv-v1", "cam"))

    def test_wrong_sensor_is_rejected(self):
        p = CameraPresets(Devices({"verified": True, "platform": "ssc30kq", "sensor": "imx415"}))
        self.assertFalse(p.selectForDevice("ssc30kq-imx335-fpv-v1", "cam"))

    def test_apply_plan_is_camera_only_and_hardware_pending(self):
        p = CameraPresets(Devices({"verified": True, "platform": "ssc30kq", "sensor": "imx335"}))
        p.selectForDevice("ssc30kq-imx335-fpv-inverted-v1", "cam")
        plan = p.buildApplyPlan()
        self.assertEqual(plan["settings"]["orientation"], "rotate_180")
        self.assertFalse(plan["appliesVideoProfile"])
        self.assertEqual(plan["execution"], "hardware-validation-pending")
        self.assertNotIn("codec", plan["settings"])
        self.assertNotIn("fps", plan["settings"])

    def test_plan_revalidates_identity_before_handoff(self):
        d = Devices({"verified": True, "platform": "ssc30kq", "sensor": "imx335"})
        p = CameraPresets(d)
        self.assertTrue(p.selectForDevice("ssc30kq-imx335-fpv-v1", "cam"))
        d.items[0]["openipcIdentity"] = {"verified": False, "platform": "ssc30kq", "sensor": "imx335"}
        self.assertEqual(p.buildApplyPlan(), {})
        self.assertFalse(p.result["ready"])


if __name__ == "__main__":
    unittest.main()
