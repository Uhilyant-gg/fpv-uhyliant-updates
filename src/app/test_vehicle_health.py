import unittest

from unified_health import HEALTH_ATTENTION, HEALTH_PROBLEM, HEALTH_READY, HEALTH_UNKNOWN
from vehicle_health import vehicle_health


class VehicleHealthTests(unittest.TestCase):
    def test_missing_snapshot_is_unknown(self):
        self.assertEqual(vehicle_health(None, None).health, HEALTH_UNKNOWN)

    def test_unconfirmed_telemetry_is_unknown(self):
        result = vehicle_health({"telemetry": {"connected": None}, "video": {"state": "playing"}}, {})
        self.assertEqual(result.health, HEALTH_UNKNOWN)
        self.assertEqual(result.reasonCode, "telemetry-not-confirmed")

    def test_runtime_error_is_problem(self):
        result = vehicle_health(
            {"telemetry": {"connected": True}, "video": {"state": "playing"}},
            {"issues": [{"severity": "error", "source": "MAVLink"}]},
        )
        self.assertEqual(result.health, HEALTH_PROBLEM)
        self.assertEqual(result.safeActions, ("diagnose",))

    def test_stalled_video_requires_attention(self):
        result = vehicle_health({"telemetry": {"connected": True}, "video": {"state": "stalled"}}, {})
        self.assertEqual(result.health, HEALTH_ATTENTION)

    def test_unmapped_video_state_fails_closed(self):
        result = vehicle_health({"telemetry": {"connected": True}, "video": {"state": "magic"}}, {})
        self.assertEqual(result.health, HEALTH_UNKNOWN)
        self.assertEqual(result.reasonCode, "video-state-unmapped")

    def test_ready_requires_confirmed_telemetry_and_known_usable_video(self):
        result = vehicle_health({"telemetry": {"connected": True}, "video": {"state": "playing"}}, {})
        self.assertEqual(result.health, HEALTH_READY)
        self.assertEqual(result.reasonCode, "vehicle-runtime-ready")


if __name__ == "__main__":
    unittest.main()
