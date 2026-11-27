"""Cross-boundary acceptance checks for the canonical E2 health contract."""

import unittest

from device_health import device_health
from station_health import station_health
from unified_health import HEALTH_PROBLEM, HEALTH_READY, HEALTH_UNKNOWN
from vehicle_health import vehicle_health


class E2UnifiedHealthAcceptanceTests(unittest.TestCase):
    def test_camera_vehicle_station_share_canonical_schema(self):
        camera = device_health(
            {
                "id": "cam-1",
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        )
        vehicle = vehicle_health(
            {"telemetry": {"connected": True}, "video": {"state": "playing"}},
            {"issues": []},
        )
        combined = station_health([camera, vehicle])
        expected = {"state", "health", "summary", "reasonCode", "evidence", "safeActions"}
        for item in (camera, vehicle, combined):
            self.assertEqual(set(item.as_dict()), expected)
        self.assertEqual(combined.health, HEALTH_READY)

    def test_missing_camera_evidence_cannot_be_promoted_by_ready_vehicle(self):
        camera = device_health(None)
        vehicle = vehicle_health(
            {"telemetry": {"connected": True}, "video": {"state": "playing"}},
            {"issues": []},
        )
        combined = station_health([camera, vehicle])
        self.assertEqual(camera.health, HEALTH_UNKNOWN)
        self.assertEqual(combined.health, HEALTH_UNKNOWN)

    def test_component_problem_remains_problem_at_station_boundary(self):
        camera = device_health(
            {
                "id": "cam-1",
                "connection": "error",
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        )
        vehicle = vehicle_health(
            {"telemetry": {"connected": True}, "video": {"state": "playing"}},
            {"issues": []},
        )
        combined = station_health([camera, vehicle])
        self.assertEqual(camera.health, HEALTH_PROBLEM)
        self.assertEqual(combined.health, HEALTH_PROBLEM)

    def test_station_does_not_promote_component_safe_actions(self):
        camera = device_health(None)
        combined = station_health([camera])
        self.assertEqual(camera.safeActions, ("find-camera",))
        self.assertEqual(combined.safeActions, ())
        self.assertEqual(combined.evidence["components"][0]["safeActions"], ["find-camera"])


if __name__ == "__main__":
    unittest.main()
