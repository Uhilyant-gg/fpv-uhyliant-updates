import unittest

from orchestrator_queue_v3_repair import authorize_repair
from orchestrator_queue_v3_runner import QueueAction, QueueDecision
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import GitHubEvidence, State


class QueueV3RepairBridgeTests(unittest.TestCase):
    def setUp(self):
        self.persisted = PersistedState(
            schema_version=SCHEMA_VERSION,
            state=State.REPAIRING,
            story_id="S1",
            baseline_sha="base",
            pr=56,
            expected_head_sha="head",
            repair_attempts=1,
            max_repair_attempts=3,
        )
        self.intent = QueueDecision(QueueAction.REPAIR, "repair-current-batch")

    def evidence(self, **kwargs):
        values = {
            "pr": 56,
            "head_sha": "head",
            "baseline_sha": "base",
            "required_checks": ("verify",),
            "successful_checks": (),
            "review_approved": False,
            "unresolved_threads": 0,
            "blocker": "required-check-failed",
        }
        values.update(kwargs)
        return GitHubEvidence(**values)

    def test_current_failed_ci_authorizes_bounded_repair(self):
        result = authorize_repair(
            queue_decision=self.intent,
            persisted=self.persisted,
            evidence=self.evidence(),
            ci_status="failed",
        )
        self.assertTrue(result.authorized)
        self.assertEqual(result.decision.attempts, 2)
        self.assertEqual(result.decision.reason_code, "repair-authorized")

    def test_non_repair_queue_action_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "queue-repair-intent-required"):
            authorize_repair(
                queue_decision=QueueDecision(QueueAction.WAIT, "ci-in-progress"),
                persisted=self.persisted,
                evidence=self.evidence(),
                ci_status="failed",
            )

    def test_wrong_repair_reason_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "queue-repair-reason-mismatch"):
            authorize_repair(
                queue_decision=QueueDecision(QueueAction.REPAIR, "unexpected"),
                persisted=self.persisted,
                evidence=self.evidence(),
                ci_status="failed",
            )

    def test_stale_evidence_is_not_authorized(self):
        result = authorize_repair(
            queue_decision=self.intent,
            persisted=self.persisted,
            evidence=self.evidence(head_sha="stale-head"),
            ci_status="failed",
        )
        self.assertFalse(result.authorized)
        self.assertEqual(result.decision.state, State.STATE_INCONSISTENT)

    def test_external_blocker_is_not_authorized(self):
        result = authorize_repair(
            queue_decision=self.intent,
            persisted=self.persisted,
            evidence=self.evidence(blocker="manual-intervention"),
            ci_status="failed",
        )
        self.assertFalse(result.authorized)
        self.assertEqual(result.decision.state, State.BLOCKED_AUTOMATION)

    def test_repair_without_failed_ci_is_not_authorized(self):
        result = authorize_repair(
            queue_decision=self.intent,
            persisted=self.persisted,
            evidence=self.evidence(),
            ci_status="green",
        )
        self.assertFalse(result.authorized)
        self.assertEqual(result.decision.reason_code, "repair-without-ci-failure")


if __name__ == "__main__":
    unittest.main()
