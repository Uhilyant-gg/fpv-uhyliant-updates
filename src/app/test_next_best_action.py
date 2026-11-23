import unittest

from next_best_action import select_next_best_action


class NextBestActionTests(unittest.TestCase):
    def test_missing_health_has_no_action(self):
        result = select_next_best_action(None)
        self.assertIsNone(result.action)
        self.assertEqual(result.reasonCode, "health-evidence-unavailable")

    def test_selects_at_most_one_explicit_safe_action(self):
        result = select_next_best_action({
            "camera": {"health": "unknown", "safeActions": ["find-camera", "diagnose"]},
        })
        self.assertEqual(result.action, "diagnose")
        self.assertEqual(result.source, "camera")

    def test_problem_precedes_unknown_then_attention_then_ready(self):
        result = select_next_best_action({
            "ready": {"health": "ready", "safeActions": ["show-video"]},
            "attention": {"health": "attention", "safeActions": ["verify-camera"]},
            "unknown": {"health": "unknown", "safeActions": ["find-camera"]},
            "problem": {"health": "problem", "safeActions": ["diagnose"]},
        })
        self.assertEqual(result.action, "diagnose")
        self.assertEqual(result.source, "problem")

    def test_unknown_action_is_not_invented_or_selected(self):
        result = select_next_best_action({
            "camera": {"health": "unknown", "safeActions": ["flash-camera"]},
        })
        self.assertIsNone(result.action)
        self.assertEqual(result.reasonCode, "no-safe-action")

    def test_deterministic_tie_break_uses_source_name(self):
        result = select_next_best_action({
            "vehicle": {"health": "unknown", "safeActions": ["diagnose"]},
            "camera": {"health": "unknown", "safeActions": ["diagnose"]},
        })
        self.assertEqual(result.source, "camera")


if __name__ == "__main__":
    unittest.main()
