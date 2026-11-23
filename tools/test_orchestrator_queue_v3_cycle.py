import unittest

from orchestrator_queue_v3 import QueueItem, build_queue
from orchestrator_queue_v3_cycle import QueueObservation, decide_cycle
from orchestrator_queue_v3_runner import QueueAction
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import State


class QueueV3CycleTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_queue(
            baseline_sha="base",
            items=[QueueItem("E2-S4", "Complete E2-S4"), QueueItem("E2-S5", "Complete E2-S5")],
        )
        self.persisted = PersistedState(
            schema_version=SCHEMA_VERSION,
            state=State.IMPLEMENTING,
            story_id="E2-S4",
            baseline_sha="base",
            pr=54,
            expected_head_sha="head",
            repair_attempts=1,
            max_repair_attempts=3,
        )

    def observe(self, **kwargs):
        values = {"baseline_sha": "base", "ci_status": "running"}
        values.update(kwargs)
        return QueueObservation(**values)

    def test_running_waits(self):
        self.assertEqual(decide_cycle(plan=self.plan, persisted=self.persisted, observation=self.observe()).action, QueueAction.WAIT)

    def test_failed_uses_persisted_repair_budget(self):
        result = decide_cycle(plan=self.plan, persisted=self.persisted, observation=self.observe(ci_status="failed"))
        self.assertEqual(result.action, QueueAction.REPAIR)

    def test_green_merged_refreshes(self):
        result = decide_cycle(plan=self.plan, persisted=self.persisted, observation=self.observe(ci_status="green", merged=True))
        self.assertEqual(result.action, QueueAction.REFRESH)

    def test_blocker_stops(self):
        result = decide_cycle(
            plan=self.plan,
            persisted=self.persisted,
            observation=self.observe(blocker_status="PHYSICAL_ACTION_REQUIRED"),
        )
        self.assertEqual(result.action, QueueAction.STOP)

    def test_stale_observed_baseline_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "runner-stale-baseline"):
            decide_cycle(plan=self.plan, persisted=self.persisted, observation=self.observe(baseline_sha="new-main"))

    def test_persisted_story_must_match_active_queue_story(self):
        stale = PersistedState(
            schema_version=SCHEMA_VERSION,
            state=State.IMPLEMENTING,
            story_id="E2-S5",
            baseline_sha="base",
            pr=54,
            expected_head_sha="head",
        )
        with self.assertRaisesRegex(ValueError, "cycle-story-binding-mismatch"):
            decide_cycle(plan=self.plan, persisted=stale, observation=self.observe())

    def test_persisted_baseline_must_match_queue(self):
        stale = PersistedState(
            schema_version=SCHEMA_VERSION,
            state=State.IMPLEMENTING,
            story_id="E2-S4",
            baseline_sha="old-base",
            pr=54,
            expected_head_sha="head",
        )
        with self.assertRaisesRegex(ValueError, "cycle-persisted-baseline-mismatch"):
            decide_cycle(plan=self.plan, persisted=stale, observation=self.observe())


if __name__ == "__main__":
    unittest.main()
