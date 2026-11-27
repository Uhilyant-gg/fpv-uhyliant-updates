import unittest

from next_action_dispatch import dispatch_intent


class NextActionDispatchTests(unittest.TestCase):
    def test_missing_action_fails_closed(self):
        result = dispatch_intent(None)
        self.assertFalse(result.accepted)
        self.assertIsNone(result.target)

    def test_safe_selected_action_maps_to_normal_ui_target(self):
        result = dispatch_intent({"action": "show-video", "reasonCode": "safe-action-selected", "source": "camera"})
        self.assertTrue(result.accepted)
        self.assertEqual(result.target, "fpv")

    def test_firmware_review_is_navigation_only(self):
        result = dispatch_intent(
            {"action": "review-firmware", "reasonCode": "safe-action-selected", "source": "camera"}
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.target, "firmware")

    def test_action_without_safe_selection_proof_is_rejected(self):
        result = dispatch_intent({"action": "diagnose", "reasonCode": "no-safe-action"})
        self.assertFalse(result.accepted)
        self.assertEqual(result.reasonCode, "next-action-not-authorized")

    def test_destructive_and_service_actions_are_never_dispatchable(self):
        for action in ("update", "fullflash", "manual-firmware", "sysupgrade", "hardware-e2e"):
            with self.subTest(action=action):
                result = dispatch_intent({"action": action, "reasonCode": "safe-action-selected"})
                self.assertFalse(result.accepted)
                self.assertIsNone(result.target)


if __name__ == "__main__":
    unittest.main()
