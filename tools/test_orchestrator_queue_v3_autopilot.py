import unittest

from orchestrator_queue_v3 import QueueItem, build_queue
from orchestrator_queue_v3_autopilot import AutopilotAction, decide_autopilot_cycle
from orchestrator_queue_v3_cycle import QueueObservation
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import GitHubEvidence, State


class QueueV3AutopilotTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_queue(baseline_sha="base", items=[QueueItem("S1", "Complete S1")])
        self.persisted = PersistedState(SCHEMA_VERSION, State.CI_RUNNING, "S1", "base", 58, "head")
        self.pr = {"number": 58, "head": {"sha": "head"}, "base": {"sha": "base"}}
        self.green_checks = [{"name": "verify", "status": "completed", "conclusion": "success", "head_sha": "head"}]

    def evidence(self, **kwargs):
        values = dict(
            pr=58,
            head_sha="head",
            base_sha="base",
            pr_story_id="S1",
            required_ci_green=False,
            security_green=True,
            review_approved=False,
            reviewed_sha="",
            tested_sha="head",
            blocker="required-check-failed",
        )
        values.update(kwargs)
        return GitHubEvidence(**values)

    def decide(self, observation, **kwargs):
        values = dict(plan=self.plan, persisted=self.persisted, observation=observation)
        values.update(kwargs)
        return decide_autopilot_cycle(**values)

    def test_running_ci_waits(self):
        result = self.decide(QueueObservation("base", "running"))
        self.assertEqual(result.action, AutopilotAction.WAIT)

    def test_human_boundary_stops(self):
        result = self.decide(QueueObservation("base", "running", blocker_status="PHYSICAL_ACTION_REQUIRED"))
        self.assertEqual(result.action, AutopilotAction.STOP)
        self.assertEqual(result.reason_code, "PHYSICAL_ACTION_REQUIRED")

    def test_failed_ci_requires_evidence(self):
        result = self.decide(QueueObservation("base", "failed"))
        self.assertEqual(result.action, AutopilotAction.STOP)
        self.assertEqual(result.reason_code, "repair-evidence-required")

    def test_failed_ci_routes_to_bounded_repair(self):
        result = self.decide(QueueObservation("base", "failed"), evidence=self.evidence())
        self.assertEqual(result.action, AutopilotAction.REPAIR)
        self.assertEqual(result.reason_code, "repair-authorized")

    def test_green_requires_merge_evidence(self):
        result = self.decide(QueueObservation("base", "green"))
        self.assertEqual(result.action, AutopilotAction.STOP)
        self.assertEqual(result.reason_code, "merge-evidence-required")

    def test_green_routes_to_existing_merge_authority(self):
        result = self.decide(
            QueueObservation("base", "green"),
            pr=self.pr,
            checks=self.green_checks,
            reviews=[],
            required_checks={"verify"},
            security_checks=set(),
        )
        self.assertEqual(result.action, AutopilotAction.MERGE_AUTHORIZED)

    def test_merged_green_routes_to_refresh(self):
        result = self.decide(QueueObservation("base", "green", merged=True))
        self.assertEqual(result.action, AutopilotAction.REFRESH)


if __name__ == "__main__":
    unittest.main()
