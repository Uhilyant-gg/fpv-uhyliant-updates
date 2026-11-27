import unittest

from orchestrator_queue_v3 import QueueItem, build_queue
from orchestrator_queue_v3_autopilot import AutopilotAction
from orchestrator_queue_v3_loop_verify import verify_repaired_head
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import GitHubEvidence, State


class QueueV3LoopVerificationTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_queue(baseline_sha="base", items=[QueueItem("S1", "Complete S1")])
        self.persisted = PersistedState(SCHEMA_VERSION, State.CI_RUNNING, "S1", "base", 65, "new-head", 1, 3)
        self.pr = {"number": 65, "head": {"sha": "new-head"}, "base": {"sha": "base"}}
        self.green_checks = [{"name": "verify", "status": "completed", "conclusion": "success", "head_sha": "new-head"}]

    def evidence(self, **kwargs):
        values = dict(
            pr=65,
            head_sha="new-head",
            base_sha="base",
            pr_story_id="S1",
            required_ci_green=True,
            security_green=True,
            review_approved=False,
            reviewed_sha="",
            tested_sha="new-head",
            blocker=None,
        )
        values.update(kwargs)
        return GitHubEvidence(**values)

    def test_green_repaired_head_reaches_existing_merge_gate(self):
        result = verify_repaired_head(
            plan=self.plan,
            persisted=self.persisted,
            evidence=self.evidence(),
            ci_status="green",
            pr=self.pr,
            checks=self.green_checks,
            reviews=[],
            required_checks={"verify"},
            security_checks=set(),
        )
        self.assertEqual(result.decision.action, AutopilotAction.MERGE_AUTHORIZED)
        self.assertEqual(result.verified_head_sha, "new-head")

    def test_running_repaired_head_waits(self):
        result = verify_repaired_head(
            plan=self.plan, persisted=self.persisted, evidence=self.evidence(), ci_status="running"
        )
        self.assertEqual(result.decision.action, AutopilotAction.WAIT)

    def test_failed_repaired_head_returns_to_bounded_repair(self):
        failed = self.evidence(required_ci_green=False, blocker="required-check-failed")
        result = verify_repaired_head(plan=self.plan, persisted=self.persisted, evidence=failed, ci_status="failed")
        self.assertEqual(result.decision.action, AutopilotAction.REPAIR)

    def test_stale_evidence_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "loop-verify-stale-evidence"):
            verify_repaired_head(
                plan=self.plan, persisted=self.persisted, evidence=self.evidence(head_sha="old-head"), ci_status="green"
            )

    def test_requires_ci_running_state(self):
        stale = PersistedState(SCHEMA_VERSION, State.REPAIRING, "S1", "base", 65, "new-head", 1, 3)
        with self.assertRaisesRegex(ValueError, "loop-verify-ci-running-required"):
            verify_repaired_head(plan=self.plan, persisted=stale, evidence=self.evidence(), ci_status="green")


if __name__ == "__main__":
    unittest.main()
