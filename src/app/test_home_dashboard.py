import unittest

from home_dashboard import home_dashboard


class HomeDashboardTests(unittest.TestCase):
    def test_no_device_is_unknown_with_find_action(self):
        result = home_dashboard([], [])
        self.assertEqual(result["health"], "unknown")
        self.assertEqual(result["title"], "Стан перевіряється")
        self.assertTrue(result["nextAction"]["available"])
        self.assertEqual(result["nextAction"]["action"], "find-camera")

    def test_verified_active_camera_with_stream_is_ready_and_shows_video(self):
        devices = [{
            "id": "cam-1",
            "name": "Camera",
            "active": True,
            "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
        }]
        streams = [{"device_id": "cam-1", "enabled": True}]
        result = home_dashboard(devices, streams)
        self.assertEqual(result["health"], "ready")
        self.assertEqual(result["title"], "Усе готово")
        self.assertEqual(result["verifiedCount"], 1)
        self.assertEqual(result["nextAction"]["action"], "show-video")

    def test_unverified_camera_gets_attention_instead_of_ready(self):
        result = home_dashboard([{
            "id": "cam-1",
            "active": True,
            "openipcIdentity": {"verified": False},
        }], [])
        self.assertEqual(result["health"], "attention")
        self.assertEqual(result["warningCount"], 1)
        self.assertEqual(result["nextAction"]["action"], "verify-camera")


if __name__ == "__main__":
    unittest.main()
