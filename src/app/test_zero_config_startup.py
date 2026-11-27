import unittest
from zero_config_startup import zero_config_startup


class ZeroConfigStartupTests(unittest.TestCase):
    def test_saved_camera_requires_revalidation_without_ready_claim(self):
        result = zero_config_startup({"verified": True, "host": "192.168.1.10"}, None, None, None)
        self.assertEqual(result["action"], "revalidate-camera")
        self.assertEqual(result["health"], "unknown")

    def test_saved_metadata_cannot_become_operational_from_unrelated_ready_fields(self):
        result = zero_config_startup(
            {"verified": True, "host": "192.168.1.10"},
            None,
            {"health": "ready", "safeActions": []},
            {"primaryId": "main", "freshPlayback": True, "health": "ready"},
        )
        self.assertEqual(result["stage"], "restore")
        self.assertEqual(result["action"], "revalidate-camera")
        self.assertNotEqual(result["health"], "ready")

    def test_verified_discovered_camera_drives_connect(self):
        result = zero_config_startup(None, {"verified": True, "host": "192.168.1.20"}, None, None)
        self.assertEqual(result["action"], "connect-camera")
        self.assertEqual(result["stage"], "discover")

    def test_missing_evidence_remains_discovery(self):
        result = zero_config_startup(None, None, None, None)
        self.assertEqual(result["action"], "find-camera")
        self.assertEqual(result["health"], "unknown")

    def test_operate_requires_fresh_ready_playback(self):
        result = zero_config_startup(
            None,
            None,
            {"health": "ready", "safeActions": []},
            {"primaryId": "main", "freshPlayback": True, "health": "ready"},
        )
        self.assertEqual(result["health"], "ready")
        self.assertEqual(result["stage"], "operate")

    def test_primary_stream_alone_does_not_claim_operational(self):
        result = zero_config_startup(None, None, {"health": "ready", "safeActions": []}, {"primaryId": "main"})
        self.assertEqual(result["stage"], "video")
        self.assertEqual(result["reasonCode"], "fresh-playback-required")


if __name__ == "__main__":
    unittest.main()
