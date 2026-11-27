import unittest

from home_dashboard import home_dashboard


class HomeDashboardTests(unittest.TestCase):
    def test_no_device_is_unknown_with_find_action(self):
        result = home_dashboard([], [])
        self.assertEqual(result["health"], "unknown")
        self.assertEqual(result["title"], "Стан перевіряється")
        self.assertTrue(result["nextAction"]["available"])
        self.assertEqual(result["nextAction"]["action"], "find-camera")
        self.assertIn("Камеру ще не додано", result["summary"])

    def test_verified_active_camera_with_stream_is_ready_and_shows_video(self):
        devices = [
            {
                "id": "cam-1",
                "name": "Camera",
                "active": True,
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        ]
        streams = [{"device_id": "cam-1", "enabled": True}]
        result = home_dashboard(devices, streams)
        self.assertEqual(result["health"], "ready")
        self.assertEqual(result["title"], "Усе готово")
        self.assertEqual(result["verifiedCount"], 1)
        self.assertEqual(result["nextAction"]["action"], "show-video")

    def test_unverified_camera_gets_attention_instead_of_ready(self):
        result = home_dashboard(
            [
                {
                    "id": "cam-1",
                    "active": True,
                    "openipcIdentity": {"verified": False},
                }
            ],
            [],
        )
        self.assertEqual(result["health"], "attention")
        self.assertEqual(result["warningCount"], 1)
        self.assertEqual(result["nextAction"]["action"], "verify-camera")
        self.assertIn("не підтверджено", result["summary"])

    def test_pending_firmware_is_hidden_from_home_and_opens_firmware_center(self):
        result = home_dashboard(
            [
                {
                    "id": "candidate",
                    "onboardingState": "pending-firmware",
                    "openipcIdentity": {"verified": True, "platform": "ssc30kq", "sensor": "imx335"},
                }
            ],
            [],
        )
        self.assertEqual(result["deviceCount"], 0)
        self.assertEqual(result["pendingCount"], 1)
        self.assertEqual(result["nextAction"]["action"], "review-firmware")
        self.assertIn("прошивку", result["summary"])

    def test_pending_video_recommends_another_camera_check(self):
        result = home_dashboard(
            [
                {
                    "id": "candidate",
                    "onboardingState": "pending-video",
                    "openipcIdentity": {"verified": True, "platform": "ssc30kq", "sensor": "imx335", "firmware": "v1"},
                }
            ],
            [],
        )
        self.assertEqual(result["deviceCount"], 0)
        self.assertEqual(result["nextAction"]["action"], "find-camera")
        self.assertIn("відеопотік", result["summary"])


if __name__ == "__main__":
    unittest.main()
