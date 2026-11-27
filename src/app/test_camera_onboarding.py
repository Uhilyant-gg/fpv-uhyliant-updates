import unittest

from camera_onboarding import camera_onboarding


class CameraOnboardingTests(unittest.TestCase):
    def candidate(self, **overrides):
        value = {
            "openipc": True,
            "identity": {
                "verified": True,
                "platform": "ssc30kq",
                "sensor": "imx335",
                "firmware": "v1.48.5.1",
            },
            "streams": [
                {"name": "Основний", "port": 554, "path": "/", "protocol": "rtsp"}
            ],
        }
        value.update(overrides)
        return value

    def test_requires_verified_supported_identity_observed_firmware_and_video(self):
        self.assertTrue(camera_onboarding(self.candidate())["ready"])
        self.assertEqual(camera_onboarding(self.candidate(streams=[]))["state"], "pending-video")
        self.assertEqual(
            camera_onboarding(self.candidate(identity={**self.candidate()["identity"], "firmware": ""}))["state"],
            "pending-firmware",
        )

    def test_unsupported_or_unverified_camera_cannot_be_staged(self):
        unsupported = self.candidate(
            identity={**self.candidate()["identity"], "sensor": "unknown-sensor"}
        )
        self.assertFalse(camera_onboarding(unsupported)["stageable"])
        unverified = self.candidate(
            identity={**self.candidate()["identity"], "verified": False}
        )
        self.assertFalse(camera_onboarding(unverified)["stageable"])

    def test_malformed_stream_does_not_make_camera_ready(self):
        result = camera_onboarding(
            self.candidate(streams=[{"name": "unverified", "path": "/"}])
        )
        self.assertFalse(result["ready"])
        self.assertEqual(result["state"], "pending-video")


if __name__ == "__main__":
    unittest.main()
