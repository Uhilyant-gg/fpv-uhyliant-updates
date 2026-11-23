import unittest
from startup_restore import startup_restore_plan


class StartupRestorePlanTests(unittest.TestCase):
    def test_verified_saved_camera_is_preferred(self):
        result = startup_restore_plan({"verified": True, "host": "192.168.1.10"}, {"verified": True, "host": "192.168.1.20"})
        self.assertEqual(result["action"], "restore-camera")
        self.assertEqual(result["host"], "192.168.1.10")

    def test_unverified_saved_camera_is_not_restored(self):
        result = startup_restore_plan({"verified": False, "host": "192.168.1.10"}, {"verified": True, "host": "192.168.1.20"})
        self.assertEqual(result["action"], "connect-camera")
        self.assertEqual(result["host"], "192.168.1.20")

    def test_missing_evidence_falls_back_to_discovery(self):
        result = startup_restore_plan(None, None)
        self.assertEqual(result, {"stage": "discover", "action": "find-camera", "host": None, "reasonCode": "no-verified-camera"})


if __name__ == "__main__":
    unittest.main()
