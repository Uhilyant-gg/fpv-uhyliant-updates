import unittest

from next_action_observability import next_action_record


class NextActionObservabilityTests(unittest.TestCase):
    def test_missing_decision_is_bounded_and_unavailable(self):
        self.assertEqual(
            next_action_record(None),
            {
                "selected": False,
                "action": None,
                "source": None,
                "reasonCode": "next-action-unavailable",
            },
        )

    def test_selected_action_records_only_bounded_fields(self):
        result = next_action_record(
            {
                "action": "diagnose",
                "source": "camera",
                "reasonCode": "safe-action-selected",
                "evidence": {"password": "must-not-copy"},
                "arbitrary": "drop-me",
            }
        )
        self.assertEqual(
            result,
            {
                "selected": True,
                "action": "diagnose",
                "source": "camera",
                "reasonCode": "safe-action-selected",
            },
        )
        self.assertNotIn("evidence", result)

    def test_non_string_values_are_not_propagated(self):
        result = next_action_record({"action": ["diagnose"], "source": {"name": "camera"}})
        self.assertFalse(result["selected"])
        self.assertIsNone(result["action"])
        self.assertIsNone(result["source"])


if __name__ == "__main__":
    unittest.main()
