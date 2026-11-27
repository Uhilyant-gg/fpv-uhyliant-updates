import unittest

from controller_profile import apply_controller_profile, calibrate_controller


MAPPING = {
    "roll": {"channel": 0, "reversed": False},
    "pitch": {"channel": 1, "reversed": True},
    "yaw": {"channel": 2, "reversed": False},
    "throttle": {"channel": 3, "reversed": False},
}
SAMPLES = [
    [1000, 1000, 1000, 1000],
    [1500, 1500, 1500, 1500],
    [2000, 2000, 2000, 2000],
]


class ControllerProfileTests(unittest.TestCase):
    def test_calibration_uses_observed_ranges_and_identity(self):
        profile = calibrate_controller(" radio-1 ", SAMPLES, MAPPING)
        self.assertEqual(profile["controllerId"], "radio-1")
        self.assertEqual(profile["calibration"][0], {"minimum": 1000, "center": 1500, "maximum": 2000})

    def test_mapping_normalizes_axes_and_throttle(self):
        profile = calibrate_controller("radio-1", SAMPLES, MAPPING)
        result = apply_controller_profile(profile, [2000, 2000, 1000, 1500])
        self.assertEqual(result, {"roll": 1.0, "pitch": -1.0, "yaw": -1.0, "throttle": 0.5})

    def test_insufficient_or_inconsistent_samples_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "samples-insufficient"):
            calibrate_controller("radio-1", SAMPLES[:2], MAPPING)
        with self.assertRaisesRegex(ValueError, "channel-count-invalid"):
            calibrate_controller("radio-1", [SAMPLES[0], [1, 2], SAMPLES[2]], MAPPING)

    def test_invalid_samples_and_identity_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "sample-invalid"):
            calibrate_controller("radio-1", [[1000, 1000, 1000, 1000], [1500, float("nan"), 1500, 1500], SAMPLES[2]], MAPPING)
        with self.assertRaisesRegex(ValueError, "identity-unavailable"):
            calibrate_controller("", SAMPLES, MAPPING)

    def test_mapping_must_assign_distinct_valid_channels(self):
        duplicate = {**MAPPING, "yaw": {"channel": 1, "reversed": False}}
        with self.assertRaisesRegex(ValueError, "mapping-invalid"):
            calibrate_controller("radio-1", SAMPLES, duplicate)
        out_of_range = {**MAPPING, "roll": {"channel": 4, "reversed": False}}
        with self.assertRaisesRegex(ValueError, "mapping-channel-invalid"):
            calibrate_controller("radio-1", SAMPLES, out_of_range)

    def test_mapped_axes_require_observed_calibration_range(self):
        samples = [[1000, 1000, 1000, 1500], [1500, 1500, 1500, 1500], [2000, 2000, 2000, 1500]]
        with self.assertRaisesRegex(ValueError, "range-invalid"):
            calibrate_controller("radio-1", samples, MAPPING)

    def test_application_fails_closed_for_out_of_range_or_malformed_input(self):
        profile = calibrate_controller("radio-1", SAMPLES, MAPPING)
        with self.assertRaisesRegex(ValueError, "outside-calibration"):
            apply_controller_profile(profile, [2100, 1500, 1500, 1500])
        with self.assertRaisesRegex(ValueError, "input-invalid"):
            apply_controller_profile(profile, [1500, 1500, 1500, True])


if __name__ == "__main__":
    unittest.main()
