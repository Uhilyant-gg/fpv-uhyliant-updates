import unittest

from controller_discovery import (
    ControllerSourceUnavailable,
    WinMMJoystickSource,
    discover_controllers,
    is_fresh,
    select_controller,
)


class FakeSource:
    def __init__(self, devices=None, error=None):
        self.devices, self.error = devices or [], error

    def poll(self):
        if self.error:
            raise self.error
        return self.devices


RADIO = {"vendorId": 0x1209, "productId": 0x4F54, "name": "EdgeTX Radio", "channels": [1000, 1500, 2000, 1200]}
OTHER = {"vendorId": 0x0483, "productId": 0x5710, "name": "Gamepad", "channels": [0, 1, 2, 3]}


def clock():
    return 100.0


class DiscoveryTests(unittest.TestCase):
    def test_missing_or_failing_source_is_unknown_not_absent(self):
        self.assertFalse(discover_controllers(None, clock)["available"])
        r = discover_controllers(FakeSource(error=ControllerSourceUnavailable("x")), clock)
        self.assertEqual(r["reasonCode"], "controller-source-unavailable")
        r = discover_controllers(FakeSource(error=OSError("boom")), clock)
        self.assertEqual(r["reasonCode"], "controller-source-failed")
        self.assertEqual(select_controller(r)["health"], "unknown")

    def test_observed_controller_has_stable_identity_and_fresh_input(self):
        r = discover_controllers(FakeSource([RADIO]), clock)
        [c] = r["controllers"]
        self.assertEqual(c["id"], "usb-hid:1209:4f54:EdgeTX Radio")
        self.assertTrue(c["connected"])
        self.assertEqual(c["channels"], [1000, 1500, 2000, 1200])
        self.assertEqual(c["observedAt"], 100.0)
        self.assertTrue(is_fresh(c, 100.5))
        self.assertFalse(is_fresh(c, 102.0))
        self.assertFalse(is_fresh({"observedAt": float("nan")}, 100.0))

    def test_invalid_channels_are_not_reported_as_live_input(self):
        r = discover_controllers(FakeSource([{**RADIO, "channels": [1, float("inf")]}]), clock)
        [c] = r["controllers"]
        self.assertFalse(c["connected"])
        self.assertIsNone(c["channels"])
        self.assertEqual(c["reasonCode"], "controller-input-unavailable")

    def test_identical_devices_are_ambiguous_and_never_guessed(self):
        r = discover_controllers(FakeSource([RADIO, dict(RADIO)]), clock)
        self.assertTrue(all(c["id"] is None for c in r["controllers"]))
        s = select_controller(r, ["usb-hid:1209:4f54:EdgeTX Radio"])
        self.assertIsNone(s["controller"])
        self.assertEqual(s["reasonCode"], "controller-identity-ambiguous")

    def test_missing_identity_fields_do_not_produce_an_id(self):
        r = discover_controllers(FakeSource([{**RADIO, "vendorId": True}, {**RADIO, "name": "  "}]), clock)
        self.assertTrue(all(c["reasonCode"] == "controller-identity-unavailable" for c in r["controllers"]))

    def test_selection_prefers_single_saved_match_otherwise_requires_choice(self):
        r = discover_controllers(FakeSource([RADIO, OTHER]), clock)
        self.assertEqual(select_controller(r)["reasonCode"], "controller-selection-required")
        s = select_controller(r, ["usb-hid:1209:4f54:EdgeTX Radio"])
        self.assertEqual(s["reasonCode"], "controller-selected-saved")
        self.assertEqual(s["controller"]["name"], "EdgeTX Radio")

    def test_no_controllers_is_unknown(self):
        s = select_controller(discover_controllers(FakeSource([]), clock))
        self.assertEqual((s["health"], s["reasonCode"]), ("unknown", "controller-not-observed"))

    def test_names_are_sanitized_and_bounded(self):
        r = discover_controllers(FakeSource([{**RADIO, "name": "Radio\x00\n" + "x" * 100}]), clock)
        self.assertEqual(len(r["controllers"][0]["name"]), 64)
        self.assertNotIn("\x00", r["controllers"][0]["id"])


class FakeWinMM:
    def joyGetNumDevs(self):
        return 3

    def joyGetPosEx(self, index, ref):
        if index == 1:
            return 167  # JOYERR_UNPLUGGED
        info = ref._obj
        info.dwXpos, info.dwYpos, info.dwZpos, info.dwRpos, info.dwUpos = 1, 2, 3, 4, 5
        return 0

    def joyGetDevCapsW(self, index, ref, size):
        caps = ref._obj
        caps.wMid, caps.wPid, caps.szPname, caps.wNumAxes = 0x1209, 0x4F54 + index, "Radio", 4
        return 0


class WinMMSourceTests(unittest.TestCase):
    def test_unplugged_slots_are_skipped_and_axes_bounded_by_caps(self):
        devices = WinMMJoystickSource(FakeWinMM()).poll()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["channels"], [1, 2, 3, 4])
        self.assertEqual(devices[1]["productId"], 0x4F56)


if __name__ == "__main__":
    unittest.main()
