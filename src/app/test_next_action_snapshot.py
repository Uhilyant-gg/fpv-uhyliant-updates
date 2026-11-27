import unittest

from next_action_snapshot import is_canonical_next_action_shape, validated_next_action_snapshot


class NextActionSnapshotTests(unittest.TestCase):
    def test_missing_snapshot_preserves_unknown_state(self):
        self.assertEqual(
            validated_next_action_snapshot(None),
            {
                "action": None,
                "reasonCode": "next-action-unavailable",
                "source": None,
            },
        )

    def test_exact_public_shape_is_canonical(self):
        value = {"action": "diagnose", "reasonCode": "safe-action-selected", "source": "camera"}
        self.assertTrue(is_canonical_next_action_shape(value))
        self.assertEqual(validated_next_action_snapshot(value), value)

    def test_extra_evidence_does_not_enter_public_snapshot(self):
        value = {
            "action": "diagnose",
            "reasonCode": "safe-action-selected",
            "source": "camera",
            "evidence": {"internal": True},
        }
        self.assertFalse(is_canonical_next_action_shape(value))
        self.assertNotIn("evidence", validated_next_action_snapshot(value))

    def test_malformed_values_fail_closed(self):
        normalized = validated_next_action_snapshot({"action": ["diagnose"], "reasonCode": None, "source": 42})
        self.assertIsNone(normalized["action"])
        self.assertIsNone(normalized["source"])
        self.assertEqual(normalized["reasonCode"], "next-action-unavailable")


if __name__ == "__main__":
    unittest.main()
