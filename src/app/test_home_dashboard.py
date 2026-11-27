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

    def _ready_camera(self):
        devices = [
            {
                "id": "cam-1",
                "name": "Camera",
                "active": True,
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        ]
        streams = [{"device_id": "cam-1", "enabled": True}]
        return devices, streams

    def test_unconfigured_controller_is_suggested_once_camera_is_ready(self):
        devices, streams = self._ready_camera()
        controller = {"health": "attention", "safeActions": ["calibrate-controller"]}
        result = home_dashboard(devices, streams, controller)
        self.assertEqual(result["nextAction"]["action"], "calibrate-controller")
        self.assertEqual(result["nextAction"]["label"], "Налаштувати пульт")

    def test_camera_actions_take_priority_over_controller_setup(self):
        controller = {"health": "attention", "safeActions": ["calibrate-controller"]}
        result = home_dashboard([], [], controller)
        self.assertEqual(result["nextAction"]["action"], "find-camera")

    def test_absent_or_ready_controller_never_adds_an_action(self):
        devices, streams = self._ready_camera()
        baseline = home_dashboard(devices, streams)["nextAction"]
        for controller in (
            None,
            {"health": "unknown", "safeActions": ["connect-controller"]},
            {"health": "ready", "safeActions": []},
            {"health": "problem", "safeActions": ["diagnose"]},
        ):
            self.assertEqual(home_dashboard(devices, streams, controller)["nextAction"], baseline, controller)

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
