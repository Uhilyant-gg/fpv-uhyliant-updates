import unittest

from next_action_presentation import present_next_action


class NextActionPresentationTests(unittest.TestCase):
    def test_missing_action_stays_unavailable(self):
        self.assertFalse(present_next_action(None)["available"])

    def test_known_action_gets_practical_label(self):
        result = present_next_action(
            {"action": "find-camera", "source": "camera", "reasonCode": "safe-action-selected"}
        )
        self.assertTrue(result["available"])
        self.assertEqual(result["label"], "Знайти камеру")
        self.assertEqual(result["source"], "camera")

    def test_unknown_or_destructive_action_is_not_presented(self):
        for action in ("invented", "fullflash", "sysupgrade"):
            with self.subTest(action=action):
                result = present_next_action({"action": action, "source": "camera"})
                self.assertFalse(result["available"])
                self.assertIsNone(result["action"])


if __name__ == "__main__":
    unittest.main()
