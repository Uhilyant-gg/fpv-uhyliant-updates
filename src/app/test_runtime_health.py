import unittest

from runtime_health import runtime_health_snapshot


class RuntimeHealthSnapshotTests(unittest.TestCase):
    def test_snapshot_exposes_same_contract_for_health_boundaries(self):
        result = runtime_health_snapshot(
            device={
                "id": "cam-1",
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            },
            vehicle_snapshot={"telemetry": {"connected": True}, "video": {"state": "playing"}},
            vehicle_diagnostics={"issues": []},
        )
        expected = {"state", "health", "summary", "reasonCode", "evidence", "safeActions"}
        self.assertEqual(set(result), {"camera", "vehicle", "station", "nextBestAction"})
        for name in ("camera", "vehicle", "station"):
            self.assertEqual(set(result[name]), expected)
        self.assertEqual(result["station"]["health"], "ready")

    def test_missing_camera_drives_find_camera_without_promoting_health(self):
        result = runtime_health_snapshot(device=None, vehicle_snapshot=None, vehicle_diagnostics=None)
        self.assertEqual(result["camera"]["health"], "unknown")
        self.assertEqual(result["vehicle"]["health"], "unknown")
        self.assertEqual(result["station"]["health"], "unknown")
        self.assertEqual(result["nextBestAction"]["action"], "find-camera")
        self.assertEqual(result["nextBestAction"]["source"], "camera")

    def test_camera_problem_drives_diagnose_and_propagates_problem(self):
        result = runtime_health_snapshot(
            device={
                "id": "cam-1",
                "connection": "error",
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            },
            vehicle_snapshot={"telemetry": {"connected": True}, "video": {"state": "playing"}},
            vehicle_diagnostics={"issues": []},
        )
        self.assertEqual(result["camera"]["health"], "problem")
        self.assertEqual(result["station"]["health"], "problem")
        self.assertEqual(result["nextBestAction"]["action"], "diagnose")
        self.assertEqual(result["nextBestAction"]["source"], "camera")


if __name__ == "__main__":
    unittest.main()
