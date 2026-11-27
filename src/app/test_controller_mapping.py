import unittest

from controller_mapping import MappingWizard, detect_moved_channel

CENTER = [1500, 1500, 1000, 1500, 1000]  # ch2 = throttle (down), ch4 = aux switch


class DetectTests(unittest.TestCase):
    def test_single_clear_movement_is_detected_with_direction(self):
        self.assertEqual(
            detect_moved_channel(CENTER, [1500, 1500, 1000, 1900, 1000]), {"channel": 3, "reversed": False}
        )
        self.assertEqual(detect_moved_channel(CENTER, [1100, 1500, 1000, 1500, 1000]), {"channel": 0, "reversed": True})

    def test_too_small_movement_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no-movement"):
            detect_moved_channel(CENTER, [1520, 1500, 1000, 1500, 1000])

    def test_two_channels_moving_together_is_ambiguous(self):
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            detect_moved_channel(CENTER, [1900, 1800, 1000, 1500, 1000])

    def test_channel_already_mapped_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "reused"):
            detect_moved_channel(CENTER, [1900, 1500, 1000, 1500, 1000], exclude=[0])

    def test_invalid_frames_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            detect_moved_channel(CENTER, [1500])
        with self.assertRaisesRegex(ValueError, "input-invalid"):
            detect_moved_channel(CENTER, [1500, float("nan"), 1000, 1500, 1000])

    def test_hid_scale_axes(self):
        center = [32767, 32767, 0, 32767]
        self.assertEqual(detect_moved_channel(center, [32767, 2000, 0, 32767]), {"channel": 1, "reversed": True})


class WizardTests(unittest.TestCase):
    def test_full_walkthrough_produces_mapping(self):
        w = MappingWizard()
        w.advance(CENTER)
        w.advance([1900, 1500, 1000, 1500, 1000])  # roll right
        w.advance([1500, 1100, 1000, 1500, 1000])  # pitch up -> reversed channel
        w.advance([1500, 1500, 1000, 1900, 1000])  # yaw right
        w.advance([1500, 1500, 2000, 1500, 1000])  # throttle up
        self.assertEqual(w.step, "sweep")
        with self.assertRaisesRegex(ValueError, "samples-insufficient"):
            w.advance(CENTER)
        for _ in range(3):
            w.observe(CENTER)
        w.advance(CENTER)
        self.assertTrue(w.done)
        self.assertEqual(
            w.mapping,
            {
                "roll": {"channel": 0, "reversed": False},
                "pitch": {"channel": 1, "reversed": True},
                "yaw": {"channel": 3, "reversed": False},
                "throttle": {"channel": 2, "reversed": False},
            },
        )

    def test_failed_step_can_be_repeated(self):
        w = MappingWizard()
        w.advance(CENTER)
        with self.assertRaises(ValueError):
            w.advance(CENTER)
        self.assertEqual(w.step, "roll")
        w.advance([1900, 1500, 1000, 1500, 1000])
        self.assertEqual(w.step, "pitch")


if __name__ == "__main__":
    unittest.main()
