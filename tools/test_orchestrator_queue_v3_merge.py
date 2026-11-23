import unittest

from orchestrator_queue_v3_merge import authorize_queue_merge
from orchestrator_queue_v3_runner import QueueAction, QueueDecision
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import State


class QueueV3MergeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.persisted = PersistedState(SCHEMA_VERSION, State.REVIEWING, "S1", "base", 57, "head")
        self.waiting = QueueDecision(QueueAction.WAIT, "awaiting-existing-merge-gate")
        self.pr = {"number": 57, "head": {"sha": "head"}, "base": {"sha": "base"}}
        self.checks = [
            {"name": "verify", "status": "completed", "conclusion": "success", "head_sha": "head"},
            {"name": "p0-security", "status": "completed", "conclusion": "success", "head_sha": "head"},
        ]

    def authorize(self, **kwargs):
        values = dict(
            queue_decision=self.waiting,
            persisted=self.persisted,
            pr=self.pr,
            checks=self.checks,
            reviews=[],
            required_checks={"verify"},
            security_checks={"p0-security"},
            protected_change=False,
            security_review_for_head=False,
        )
        values.update(kwargs)
        return authorize_queue_merge(**values)

    def test_green_wait_state_delegates_to_existing_merge_authority(self):
        result = self.authorize()
        self.assertTrue(result.authorized)
        self.assertEqual(result.reason_code, "merge-authorized")

    def test_non_wait_action_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "queue-merge-wait-required"):
            self.authorize(queue_decision=QueueDecision(QueueAction.REPAIR, "repair-current-batch"))

    def test_wrong_wait_reason_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "queue-merge-gate-reason-required"):
            self.authorize(queue_decision=QueueDecision(QueueAction.WAIT, "ci-in-progress"))

    def test_stale_pr_head_is_not_authorized(self):
        stale = {"number": 57, "head": {"sha": "new-head"}, "base": {"sha": "base"}}
        result = self.authorize(pr=stale)
        self.assertFalse(result.authorized)
        self.assertEqual(result.reason_code, "stale-execution")

    def test_protected_change_requires_security_review(self):
        result = self.authorize(protected_change=True, security_review_for_head=False)
        self.assertFalse(result.authorized)
        self.assertEqual(result.reason_code, "security-review-required")


if __name__ == "__main__":
    unittest.main()
