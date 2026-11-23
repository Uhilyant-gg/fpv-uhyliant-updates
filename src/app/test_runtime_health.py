import unittest

from runtime_health import runtime_health_snapshot


class RuntimeHealthSnapshotTests(unittest.TestCase):
    def test_composes_health_and_next_action(self):
        result = runtime_health_snapshot(
            device=None,
            vehicle_snapshot=None,
            vehicle_diagnostics=None,
        )
        expected = {"state", "health", "summary", "reasonCode", "evidence", "safeActions"}
        self.assertEqual(
            set(result),
            {"camera", "vehicle", "station", "nextBestAction", "zeroConfigStartup"},
        )
        for name in ("camera", "vehicle", "station"):
            self.assertEqual(set(result[name]), expected)
        self.assertEqual(result["station"]["health"], "unknown")
        self.assertEqual(result["nextBestAction"]["action"], "find-camera")
        self.assertEqual(result["nextBestAction"]["source"], "camera")
        self.assertEqual(result["zeroConfigStartup"]["stage"], "camera")
        self.assertEqual(result["zeroConfigStartup"]["health"], "unknown")

    def test_ready_camera_requires_video_before_operate(self):
        result = runtime_health_snapshot(
            device={
                "reachable": True,
                "openipcVerified": True,
                "identity": {"platform": "ssc338q", "sensor": "imx335"},
            },
            vehicle_snapshot=None,
            vehicle_diagnostics=None,
            workspace=None,
        )
        if result["camera"]["health"] == "ready":
            self.assertEqual(result["zeroConfigStartup"]["stage"], "video")
            self.assertNotEqual(result["zeroConfigStartup"]["health"], "ready")


if __name__ == "__main__":
    unittest.main()
