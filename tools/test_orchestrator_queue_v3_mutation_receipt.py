import unittest

from orchestrator_queue_v3_mutation import MutationPlan
from orchestrator_queue_v3_mutation_receipt import MutationReceipt, accept_mutation_receipt
from orchestrator_v2 import State


class QueueV3MutationReceiptTests(unittest.TestCase):
    def setUp(self):
        self.plan = MutationPlan("copilot/repair-s1", "old-head", (("app/a.py", "fixed\n"),), State.CI_RUNNING)

    def test_exact_receipt_returns_ci_running_with_new_head(self):
        result = accept_mutation_receipt(
            plan=self.plan,
            receipt=MutationReceipt("copilot/repair-s1", "old-head", "new-head"),
        )
        self.assertEqual(result.branch, "copilot/repair-s1")
        self.assertEqual(result.new_head_sha, "new-head")
        self.assertEqual(result.next_state, State.CI_RUNNING)

    def test_branch_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "mutation-receipt-branch-mismatch"):
            accept_mutation_receipt(
                plan=self.plan,
                receipt=MutationReceipt("copilot/other", "old-head", "new-head"),
            )

    def test_stale_previous_head_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "mutation-receipt-stale-head"):
            accept_mutation_receipt(
                plan=self.plan,
                receipt=MutationReceipt("copilot/repair-s1", "different-head", "new-head"),
            )

    def test_unchanged_head_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "mutation-head-did-not-change"):
            accept_mutation_receipt(
                plan=self.plan,
                receipt=MutationReceipt("copilot/repair-s1", "old-head", "old-head"),
            )


if __name__ == "__main__":
    unittest.main()
