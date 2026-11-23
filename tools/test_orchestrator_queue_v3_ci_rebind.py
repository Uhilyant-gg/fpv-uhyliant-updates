import unittest

from orchestrator_queue_v3_ci_rebind import rebind_after_mutation
from orchestrator_queue_v3_mutation_receipt import MutationOutcome
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import State


class QueueV3CiRebindTests(unittest.TestCase):
    def setUp(self):
        self.persisted = PersistedState(
            SCHEMA_VERSION, State.REPAIRING, "S1", "base", 64, "old-head", repair_attempts=1, max_repair_attempts=3
        )
        self.outcome = MutationOutcome("copilot/repair-s1", "new-head", State.CI_RUNNING)

    def test_rebinds_expected_head_and_returns_to_ci(self):
        result = rebind_after_mutation(persisted=self.persisted, outcome=self.outcome)
        self.assertEqual(result.state, State.CI_RUNNING)
        self.assertEqual(result.expected_head_sha, "new-head")
        self.assertEqual(result.baseline_sha, "base")
        self.assertEqual(result.story_id, "S1")
        self.assertEqual(result.repair_attempts, 2)

    def test_requires_repairing_state(self):
        stale = PersistedState(SCHEMA_VERSION, State.CI_FAILED, "S1", "base", 64, "old-head")
        with self.assertRaisesRegex(ValueError, "ci-rebind-repair-state-required"):
            rebind_after_mutation(persisted=stale, outcome=self.outcome)

    def test_requires_ci_running_outcome(self):
        with self.assertRaisesRegex(ValueError, "ci-rebind-running-state-required"):
            rebind_after_mutation(
                persisted=self.persisted,
                outcome=MutationOutcome("copilot/repair-s1", "new-head", State.REPAIRING),
            )

    def test_head_must_change(self):
        with self.assertRaisesRegex(ValueError, "ci-rebind-head-must-change"):
            rebind_after_mutation(
                persisted=self.persisted,
                outcome=MutationOutcome("copilot/repair-s1", "old-head", State.CI_RUNNING),
            )

    def test_repair_budget_remains_bounded(self):
        exhausted = PersistedState(
            SCHEMA_VERSION, State.REPAIRING, "S1", "base", 64, "old-head", repair_attempts=3, max_repair_attempts=3
        )
        with self.assertRaisesRegex(ValueError, "invalid repair budget"):
            rebind_after_mutation(persisted=exhausted, outcome=self.outcome)


if __name__ == "__main__":
    unittest.main()
