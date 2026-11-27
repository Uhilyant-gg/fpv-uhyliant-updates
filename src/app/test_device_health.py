import unittest

from device_health import device_health
from unified_health import HEALTH_ATTENTION, HEALTH_PROBLEM, HEALTH_READY, HEALTH_UNKNOWN


class DeviceHealthTests(unittest.TestCase):
    def test_missing_device_is_unknown(self):
        result = device_health(None)
        self.assertEqual(result.health, HEALTH_UNKNOWN)
        self.assertEqual(result.safeActions, ("find-camera",))

    def test_saved_device_without_fresh_identity_is_unknown(self):
        result = device_health({"id": "camera-1", "host": "192.168.1.10", "openipcIdentity": {}})
        self.assertEqual(result.health, HEALTH_UNKNOWN)
        self.assertEqual(result.reasonCode, "device-identity-unknown")

    def test_unverified_identity_never_becomes_ready(self):
        result = device_health({"id": "camera-1", "openipcIdentity": {"verified": False}})
        self.assertEqual(result.health, HEALTH_ATTENTION)
        self.assertNotEqual(result.health, HEALTH_READY)

    def test_verified_without_platform_or_sensor_stays_unknown(self):
        result = device_health({"id": "camera-1", "openipcIdentity": {"verified": True, "platform": "ssc338q"}})
        self.assertEqual(result.health, HEALTH_UNKNOWN)
        self.assertEqual(result.reasonCode, "hardware-identity-incomplete")

    def test_verified_disconnected_camera_requests_connect(self):
        result = device_health(
            {
                "id": "camera-1",
                "connection": "disconnected",
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        )
        self.assertEqual(result.health, HEALTH_ATTENTION)
        self.assertEqual(result.safeActions, ("connect-camera",))

    def test_observed_stream_exposes_show_video(self):
        result = device_health(
            {
                "id": "camera-1",
                "connection": "ssh",
                "streams": [{"id": "main"}],
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        )
        self.assertEqual(result.health, HEALTH_READY)
        self.assertEqual(result.safeActions, ("show-video",))

    def test_observed_verified_identity_can_be_ready(self):
        result = device_health(
            {
                "id": "camera-1",
                "connection": "ssh",
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        )
        self.assertEqual(result.health, HEALTH_READY)

    def test_reported_connection_error_is_problem_after_identity_is_observed(self):
        result = device_health(
            {
                "id": "camera-1",
                "connection": "error",
                "openipcIdentity": {"verified": True, "platform": "ssc338q", "sensor": "imx335"},
            }
        )
        self.assertEqual(result.health, HEALTH_PROBLEM)
        self.assertEqual(result.safeActions, ("diagnose",))


if __name__ == "__main__":
    unittest.main()
