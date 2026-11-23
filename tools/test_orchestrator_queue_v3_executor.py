import unittest

from orchestrator_queue_v3_autopilot import AutopilotAction, AutopilotDecision
from orchestrator_queue_v3_executor import prepare_repair_handoff
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import State


class QueueV3ExecutorHandoffTests(unittest.TestCase):
    def setUp(self):
        self.persisted = PersistedState(SCHEMA_VERSION, State.REPAIRING, "S1", "base", 59, "head")
        self.authorized = AutopilotDecision(AutopilotAction.REPAIR, "repair-authorized")

    def test_authorized_repair_builds_bound_executor_request(self):
        plan = prepare_repair_handoff(
            decision=self.authorized,
            persisted=self.persisted,
            objective="Repair failed CI",
            max_steps=4,
            allowed_outputs=["patch-proposal"],
        )
        self.assertEqual(plan.story_id, "S1")
        self.assertEqual(plan.baseline_sha, "base")
        self.assertEqual(plan.state, State.REPAIRING)
        self.assertEqual(plan.request["storyId"], "S1")
        self.assertEqual(plan.request["baselineSha"], "base")
        self.assertEqual(plan.request["maxSteps"], 4)

    def test_non_repair_action_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "executor-repair-authorization-required"):
            prepare_repair_handoff(
                decision=AutopilotDecision(AutopilotAction.WAIT, "ci-in-progress"),
                persisted=self.persisted,
                objective="Repair failed CI",
            )

    def test_wrong_repair_reason_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "executor-repair-reason-mismatch"):
            prepare_repair_handoff(
                decision=AutopilotDecision(AutopilotAction.REPAIR, "unexpected"),
                persisted=self.persisted,
                objective="Repair failed CI",
            )

    def test_non_repairing_persisted_state_fails_closed(self):
        persisted = PersistedState(SCHEMA_VERSION, State.CI_FAILED, "S1", "base", 59, "head")
        with self.assertRaisesRegex(ValueError, "executor-repair-state-required"):
            prepare_repair_handoff(decision=self.authorized, persisted=persisted, objective="Repair failed CI")


if __name__ == "__main__":
    unittest.main()
