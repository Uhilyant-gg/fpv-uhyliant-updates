import tempfile
import unittest
from pathlib import Path

from controller_onboarding import ControllerOnboarding
from controller_profile_store import JsonControllerProfileStore

RADIO_ID = "usb-hid:1209:4f54:EdgeTX Radio"
MAPPING = {
    "roll": {"channel": 0, "reversed": False},
    "pitch": {"channel": 1, "reversed": False},
    "yaw": {"channel": 2, "reversed": False},
    "throttle": {"channel": 3, "reversed": False},
}


class LiveSource:
    def __init__(self):
        self.frames = [[1500, 1500, 1500, 1000]]
        self.present = True

    def poll(self):
        if not self.present:
            return []
        return [{"vendorId": 0x1209, "productId": 0x4F54, "name": "EdgeTX Radio", "channels": self.frames[0]}]


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "controllers.json"
        self.store = JsonControllerProfileStore(self.path)
        self.source = LiveSource()
        self.flow = ControllerOnboarding(self.source, self.store, Clock())

    def tearDown(self):
        self.tmp.cleanup()

    def _calibrate(self):
        self.assertEqual(self.flow.begin_calibration()["reasonCode"], "controller-calibration-in-progress")
        for frame in ([1000, 1000, 1000, 1000], [2000, 2000, 2000, 2000], [1500, 1500, 1500, 1500]):
            self.source.frames[0] = frame
            self.assertEqual(self.flow.sample()["reasonCode"], "controller-calibration-in-progress")
        return self.flow.finish_calibration(MAPPING)

    def test_no_source_is_unknown(self):
        r = ControllerOnboarding(None, self.store).refresh()
        self.assertEqual((r["health"], r["restored"]), ("unknown", False))

    def test_new_controller_needs_calibration(self):
        r = self.flow.refresh()
        self.assertEqual((r["health"], r["reasonCode"]), ("attention", "controller-profile-unavailable"))
        self.assertEqual(r["safeActions"], ["calibrate-controller"])
        self.assertEqual(r["controller"]["id"], RADIO_ID)

    def test_calibration_persists_and_restores_with_fresh_input(self):
        r = self._calibrate()
        self.assertTrue(r["restored"], r)
        self.assertEqual(r["health"], "ready")
        self.assertEqual(r["controls"], {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "throttle": 0.5})
        self.assertIn(RADIO_ID, self.store.load())
        # A new session restores from disk, but only with a live matching observation.
        restarted = ControllerOnboarding(self.source, JsonControllerProfileStore(self.path), Clock())
        self.assertTrue(restarted.refresh()["restored"])
        self.source.present = False
        r = restarted.refresh()
        self.assertEqual((r["health"], r["restored"], r["safeActions"]), ("unknown", False, ["connect-controller"]))

    def test_out_of_calibration_input_asks_for_recalibration(self):
        self._calibrate()
        self.source.frames[0] = [2500, 1500, 1500, 1500]
        r = self.flow.refresh()
        self.assertEqual((r["health"], r["reasonCode"]), ("problem", "controller-input-outside-calibration"))
        self.assertEqual(r["safeActions"], ["calibrate-controller"])

    def test_unplug_during_calibration_interrupts_without_saving(self):
        self.flow.begin_calibration()
        self.source.present = False
        r = self.flow.sample()
        self.assertEqual(r["reasonCode"], "controller-calibration-interrupted")
        self.assertFalse(r["calibration"]["active"])
        self.assertEqual(self.store.load(), {})

    def test_insufficient_movement_is_rejected_and_nothing_saved(self):
        self.flow.begin_calibration()
        self.flow.sample()
        self.flow.sample()
        r = self.flow.finish_calibration(MAPPING)
        self.assertEqual(r["reasonCode"], "controller-calibration-range-invalid")
        self.assertEqual(self.store.load(), {})

    def test_corrupt_store_is_reported_not_overwritten(self):
        self.path.write_text("garbage", encoding="utf-8")
        r = self.flow.refresh()
        self.assertEqual((r["health"], r["reasonCode"]), ("problem", "controller-profile-store-invalid"))
        r = self._calibrate()
        self.assertEqual(r["health"], "problem")
        self.assertEqual(self.path.read_text(encoding="utf-8"), "garbage")

    def test_finish_without_session(self):
        self.assertEqual(self.flow.finish_calibration(MAPPING)["reasonCode"], "controller-calibration-not-started")


if __name__ == "__main__":
    unittest.main()
