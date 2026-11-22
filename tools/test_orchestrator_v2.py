import unittest
from orchestrator_v2 import Binding, State, execution_is_current, hardware_verified, merge_eligible, next_repair_attempt, reconcile, validate_transition


class OrchestratorP0(unittest.TestCase):
    def setUp(self):
        self.binding = Binding("E2-S1", "base", 24, "head")

    def test_state_machine_fail_closed(self):
        self.assertTrue(validate_transition(State.READY, State.PLANNING))
        self.assertFalse(validate_transition(State.READY, State.MERGING))

    def test_stale_execution_cannot_mutate_current_state(self):
        self.assertTrue(execution_is_current(self.binding, story_id="E2-S1", baseline_sha="base", pr=24, head_sha="head"))
        self.assertFalse(execution_is_current(self.binding, story_id="E2-S1", baseline_sha="base", pr=24, head_sha="new-head"))

    def test_repair_loop_is_bounded(self):
        self.assertEqual(next_repair_attempt(0, 2), (State.REPAIRING, 1))
        self.assertEqual(next_repair_attempt(2, 2), (State.BLOCKED_AUTOMATION, 2))

    def test_merge_gate_binds_review_and_ci_to_head(self):
        good=dict(binding_current=True, ci_green=True, security_green=True, review_approved=True,
                  reviewed_sha="head", tested_sha="head", current_head_sha="head",
                  pr_story_id="E2-S1", active_story_id="E2-S1", blocker=None)
        self.assertTrue(merge_eligible(**good))
        good["reviewed_sha"]="old"
        self.assertFalse(merge_eligible(**good))

    def test_security_ambiguity_fails_closed(self):
        self.assertEqual(reconcile(persisted=State.REVIEWING, pr_exists=True, pr_merged=False,
                                   ci_status=None, binding_current=True), State.STATE_INCONSISTENT)

    def test_reconcile_rejects_stale_binding(self):
        self.assertEqual(reconcile(persisted=State.CI_RUNNING, pr_exists=True, pr_merged=False,
                                   ci_status="green", binding_current=False), State.STATE_INCONSISTENT)

    def test_software_evidence_is_not_hardware_verification(self):
        self.assertFalse(hardware_verified(physical_evidence=False, ci_passed=True, mock_passed=True,
                                           simulation_passed=True, ai_claimed_success=True))
        self.assertTrue(hardware_verified(physical_evidence=True))


if __name__ == "__main__":
    unittest.main()
