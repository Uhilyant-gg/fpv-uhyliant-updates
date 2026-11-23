import unittest
from startup_restore import startup_restore_plan


class StartupRestorePlanTests(unittest.TestCase):
    def test_saved_camera_requires_revalidation(self):
        result = startup_restore_plan({"verified": True, "host": "192.168.1.10"}, None)
        self.assertEqual(result["action"], "revalidate-camera")
        self.assertEqual(result["host"], "192.168.1.10")
        self.assertEqual(result["reasonCode"], "saved-camera-revalidation-required")

    def test_fresh_discovery_is_preferred_over_saved_metadata(self):
        result = startup_restore_plan({"verified": True, "host": "192.168.1.10"}, {"verified": True, "host": "192.168.1.20"})
        self.assertEqual(result["action"], "connect-camera")
        self.assertEqual(result["host"], "192.168.1.20")

    def test_unverified_saved_camera_does_not_block_fresh_discovery(self):
        result = startup_restore_plan({"verified": False, "host": "192.168.1.10"}, {"verified": True, "host": "192.168.1.20"})
        self.assertEqual(result["action"], "connect-camera")
        self.assertEqual(result["host"], "192.168.1.20")

    def test_missing_evidence_falls_back_to_discovery(self):
        result = startup_restore_plan(None, None)
        self.assertEqual(result, {"stage": "discover", "action": "find-camera", "host": None, "reasonCode": "no-verified-camera"})


if __name__ == "__main__":
    unittest.main()
