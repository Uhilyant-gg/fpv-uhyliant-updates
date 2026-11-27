import unittest
from orchestrator_v2 import (
    Binding,
    GitHubEvidence,
    State,
    evidence_binding_current,
    execution_is_current,
    hardware_verified,
    is_protected_path,
    merge_eligible,
    merge_eligible_from_evidence,
    next_repair_attempt,
    protected_change_requires_security_review,
    reconcile,
    reconcile_evidence,
    validate_transition,
)


class OrchestratorP0(unittest.TestCase):
    def setUp(self):
        self.binding = Binding("ORCH-S2", "base", 28, "head")
        self.evidence = GitHubEvidence(28, "head", "base", "ORCH-S2", True, True, True, "head", "head")

    def test_state_machine_fail_closed(self):
        self.assertTrue(validate_transition(State.READY, State.PLANNING))
        self.assertFalse(validate_transition(State.READY, State.MERGING))

    def test_stale_execution_cannot_mutate_current_state(self):
        self.assertTrue(
            execution_is_current(self.binding, story_id="ORCH-S2", baseline_sha="base", pr=28, head_sha="head")
        )
        self.assertFalse(
            execution_is_current(self.binding, story_id="ORCH-S2", baseline_sha="base", pr=28, head_sha="new-head")
        )

    def test_factual_evidence_binding_includes_baseline(self):
        self.assertTrue(evidence_binding_current(self.binding, self.evidence))
        stale = GitHubEvidence(28, "head", "new-base", "ORCH-S2", True, True, True, "head", "head")
        self.assertFalse(evidence_binding_current(self.binding, stale))

    def test_repair_loop_is_bounded(self):
        self.assertEqual(next_repair_attempt(0, 2), (State.REPAIRING, 1))
        self.assertEqual(next_repair_attempt(2, 2), (State.BLOCKED_AUTOMATION, 2))

    def test_merge_gate_requires_exact_factual_evidence(self):
        self.assertTrue(merge_eligible_from_evidence(self.binding, self.evidence))
        for field, value in (
            ("tested_sha", "old"),
            ("reviewed_sha", "old"),
            ("security_green", False),
            ("review_approved", False),
        ):
            data = self.evidence.__dict__.copy()
            data[field] = value
            self.assertFalse(merge_eligible_from_evidence(self.binding, GitHubEvidence(**data)))

    def test_legacy_merge_gate_binds_review_and_ci_to_head(self):
        good = dict(
            binding_current=True,
            ci_green=True,
            security_green=True,
            review_approved=True,
            reviewed_sha="head",
            tested_sha="head",
            current_head_sha="head",
            pr_story_id="ORCH-S2",
            active_story_id="ORCH-S2",
            blocker=None,
        )
        self.assertTrue(merge_eligible(**good))
        good["reviewed_sha"] = "old"
        self.assertFalse(merge_eligible(**good))

    def test_reconciliation_uses_same_binding(self):
        self.assertEqual(
            reconcile_evidence(
                persisted=State.CI_RUNNING, binding=self.binding, evidence=self.evidence, ci_status="green"
            ),
            State.REVIEWING,
        )
        stale = GitHubEvidence(28, "other", "base", "ORCH-S2", True, True, True, "other", "other")
        self.assertEqual(
            reconcile_evidence(persisted=State.CI_RUNNING, binding=self.binding, evidence=stale, ci_status="green"),
            State.STATE_INCONSISTENT,
        )

    def test_security_ambiguity_fails_closed(self):
        self.assertEqual(
            reconcile(persisted=State.REVIEWING, pr_exists=True, pr_merged=False, ci_status=None, binding_current=True),
            State.STATE_INCONSISTENT,
        )

    def test_protected_control_plane_changes_require_review(self):
        protected = [
            "ORCHESTRATOR_V2.md",
            ".github/workflows/x.yml",
            "tools/orchestrator_v2.py",
            "features/orchestrator_v2_security.feature",
        ]
        for path in protected:
            self.assertTrue(is_protected_path(path), path)
        self.assertTrue(protected_change_requires_security_review(protected))
        self.assertFalse(protected_change_requires_security_review(["src/app/main.py"]))

    def test_software_evidence_is_not_hardware_verification(self):
        self.assertFalse(
            hardware_verified(
                physical_evidence=False,
                ci_passed=True,
                mock_passed=True,
                simulation_passed=True,
                ai_claimed_success=True,
            )
        )
        self.assertTrue(hardware_verified(physical_evidence=True))


if __name__ == "__main__":
    unittest.main()
