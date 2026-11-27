import unittest
from vehicle_health import vehicle_health


class VehicleHealthNextActionTests(unittest.TestCase):
    def test_idle_video_with_confirmed_telemetry_exposes_show_video(self):
        result = vehicle_health({"telemetry": {"connected": True}, "video": {"state": "idle"}}, {"issues": []})
        self.assertEqual(result.safeActions, ("show-video",))
        self.assertEqual(result.health, "unknown")

    def test_unmapped_video_does_not_invent_action(self):
        result = vehicle_health({"telemetry": {"connected": True}, "video": {"state": "future-state"}}, {"issues": []})
        self.assertEqual(result.safeActions, ())


if __name__ == "__main__":
    unittest.main()
