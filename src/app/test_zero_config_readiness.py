import unittest
from zero_config_readiness import zero_config_readiness


class ZeroConfigReadinessTests(unittest.TestCase):
    def test_missing_camera_starts_discovery(self):
        self.assertEqual(zero_config_readiness(None, None)["action"], "find-camera")

    def test_unknown_camera_is_not_promoted(self):
        result = zero_config_readiness(
            {"health": "unknown", "reasonCode": "identity-unknown", "safeActions": ["identify-camera"]}, None
        )
        self.assertEqual(result["health"], "unknown")
        self.assertEqual(result["action"], "identify-camera")

    def test_ready_camera_without_primary_stream_requests_video(self):
        result = zero_config_readiness({"health": "ready", "safeActions": []}, {"primaryId": ""})
        self.assertEqual(result["health"], "attention")
        self.assertEqual(result["action"], "show-video")

    def test_primary_stream_without_fresh_playback_is_not_operational(self):
        result = zero_config_readiness({"health": "ready", "safeActions": []}, {"primaryId": "main", "health": "ready"})
        self.assertEqual(result["health"], "attention")
        self.assertEqual(result["action"], "reconnect-video")
        self.assertEqual(result["reasonCode"], "fresh-playback-required")

    def test_fresh_playback_with_unready_runtime_requires_diagnosis(self):
        result = zero_config_readiness(
            {"health": "ready", "safeActions": []},
            {"primaryId": "main", "freshPlayback": True, "health": "problem", "reasonCode": "video-stalled"},
        )
        self.assertEqual(result["stage"], "video")
        self.assertEqual(result["action"], "diagnose")
        self.assertEqual(result["reasonCode"], "video-stalled")

    def test_ready_camera_primary_stream_and_fresh_ready_playback_reach_operate(self):
        result = zero_config_readiness(
            {"health": "ready", "safeActions": []}, {"primaryId": "main", "freshPlayback": True, "health": "ready"}
        )
        self.assertEqual(result["health"], "ready")
        self.assertEqual(result["stage"], "operate")
        self.assertIsNone(result["action"])


if __name__ == "__main__":
    unittest.main()
