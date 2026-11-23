import unittest
from zero_config_startup import zero_config_startup


class ZeroConfigStartupTests(unittest.TestCase):
    def test_verified_saved_camera_drives_restore_without_ready_claim(self):
        result = zero_config_startup({"verified": True, "host": "192.168.1.10"}, None, None, None)
        self.assertEqual(result["action"], "restore-camera")
        self.assertNotEqual(result["health"], "ready")

    def test_verified_discovered_camera_drives_connect(self):
        result = zero_config_startup(None, {"verified": True, "host": "192.168.1.20"}, None, None)
        self.assertEqual(result["action"], "connect-camera")
        self.assertEqual(result["stage"], "discover")

    def test_missing_evidence_remains_discovery(self):
        result = zero_config_startup(None, None, None, None)
        self.assertEqual(result["action"], "find-camera")
        self.assertEqual(result["health"], "unknown")

    def test_operate_requires_ready_camera_and_primary_stream(self):
        result = zero_config_startup(None, None, {"health": "ready", "safeActions": []}, {"primaryId": "main"})
        self.assertEqual(result["health"], "ready")
        self.assertEqual(result["stage"], "operate")


if __name__ == "__main__":
    unittest.main()
