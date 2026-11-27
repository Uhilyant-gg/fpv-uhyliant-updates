import unittest
from station_action_summary import station_action_summary


class StationActionSummaryTests(unittest.TestCase):
    def test_no_action_stays_explicit(self):
        self.assertEqual(station_action_summary(None)["hasAction"], False)

    def test_selected_action_preserves_source_and_reason(self):
        result = station_action_summary(
            {"action": "diagnose", "source": "camera", "reasonCode": "safe-action-selected"}
        )
        self.assertTrue(result["hasAction"])
        self.assertEqual(result["source"], "camera")
        self.assertEqual(result["reasonCode"], "safe-action-selected")

    def test_non_string_action_is_rejected(self):
        self.assertFalse(station_action_summary({"action": ["diagnose"]})["hasAction"])


if __name__ == "__main__":
    unittest.main()
