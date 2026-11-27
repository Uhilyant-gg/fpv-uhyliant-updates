import unittest
from action_safety_policy import can_auto_dispatch, classify_action


class ActionSafetyPolicyTests(unittest.TestCase):
    def test_normal_navigation_can_auto_dispatch(self):
        self.assertTrue(can_auto_dispatch("show-video"))
        self.assertEqual(classify_action("diagnose"), "normal")

    def test_destructive_and_service_actions_are_guarded(self):
        for action in ("update", "fullflash", "manual-firmware", "sysupgrade", "hardware-e2e"):
            with self.subTest(action=action):
                self.assertEqual(classify_action(action), "guarded")
                self.assertFalse(can_auto_dispatch(action))

    def test_unknown_action_fails_closed(self):
        self.assertEqual(classify_action("future-action"), "unknown")
        self.assertFalse(can_auto_dispatch("future-action"))


if __name__ == "__main__":
    unittest.main()
