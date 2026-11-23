import unittest

from orchestrator_queue_v3 import QueueItem, build_queue
from orchestrator_queue_v3_runner import QueueAction, decide_queue_action


class QueueV3RunnerTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_queue(
            baseline_sha="base",
            items=[QueueItem("E2-S4", "Complete E2-S4"), QueueItem("E2-S5", "Complete E2-S5")],
        )

    def decide(self, **kwargs):
        values = {"active_story_id": "E2-S4", "ci_status": "running"}
        values.update(kwargs)
        return decide_queue_action(self.plan, **values)

    def test_running_ci_waits(self):
        self.assertEqual(self.decide().action, QueueAction.WAIT)

    def test_failed_ci_repairs_current_batch(self):
        result = self.decide(ci_status="failed", repair_attempts=1, max_repair_attempts=3)
        self.assertEqual(result.action, QueueAction.REPAIR)
        self.assertEqual(result.reason_code, "repair-current-batch")

    def test_exhausted_repair_budget_stops(self):
        result = self.decide(ci_status="failed", repair_attempts=3, max_repair_attempts=3)
        self.assertEqual(result.action, QueueAction.STOP)
        self.assertEqual(result.reason_code, "repair-budget-exceeded")

    def test_green_waits_for_existing_merge_authority(self):
        result = self.decide(ci_status="green")
        self.assertEqual(result.action, QueueAction.WAIT)
        self.assertEqual(result.reason_code, "awaiting-existing-merge-gate")

    def test_merged_green_requires_fresh_queue_refresh(self):
        result = self.decide(ci_status="green", merged=True)
        self.assertEqual(result.action, QueueAction.REFRESH)
        self.assertEqual(result.reason_code, "post-merge-refresh-required")

    def test_merged_without_green_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "runner-merged-without-green-ci"):
            self.decide(ci_status="failed", merged=True)

    def test_physical_secret_and_product_blockers_stop(self):
        for blocker in ("PHYSICAL_ACTION_REQUIRED", "SECRET_REQUIRED", "PRODUCT_DECISION_REQUIRED"):
            with self.subTest(blocker=blocker):
                self.assertEqual(self.decide(blocker_status=blocker).action, QueueAction.STOP)

    def test_stale_active_story_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "runner-active-story-mismatch"):
            self.decide(active_story_id="E2-S5")

    def test_unknown_ci_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "runner-unknown-ci-status"):
            self.decide(ci_status="mystery")


if __name__ == "__main__":
    unittest.main()
