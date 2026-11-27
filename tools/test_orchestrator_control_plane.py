import unittest
from orchestrator_control_plane import accept_result, prepare_invocation
from orchestrator_state import PersistedState
from orchestrator_v2 import State


class ExecutorControlPlaneTests(unittest.TestCase):
    def state(self, state=State.IMPLEMENTING, story="ORCH-S10", baseline="base"):
        return PersistedState(1, state, story, baseline, 40, "head", 0, 3)

    def result(self, plan, **kw):
        data = {
            "schemaVersion": 1,
            "requestDigest": plan.request["requestDigest"],
            "storyId": plan.story_id,
            "baselineSha": plan.baseline_sha,
            "stepsUsed": 2,
            "outputType": "patch-proposal",
            "payload": "proposal",
            "stopReason": None,
        }
        data.update(kw)
        return data

    def test_prepare_binds_persisted_story_baseline_and_state(self):
        plan = prepare_invocation(persisted=self.state(), objective="bounded work", max_steps=5)
        self.assertEqual(plan.request["storyId"], "ORCH-S10")
        self.assertEqual(plan.request["baselineSha"], "base")
        self.assertEqual(plan.request["state"], "IMPLEMENTING")

    def test_ready_result_cannot_advance_lifecycle(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        accepted = accept_result(persisted=state, plan=plan, result_payload=self.result(plan))
        self.assertEqual(accepted.state, State.IMPLEMENTING)

    def test_stale_persisted_story_is_denied(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        with self.assertRaises(ValueError):
            accept_result(persisted=self.state(story="new"), plan=plan, result_payload=self.result(plan))

    def test_stale_persisted_baseline_is_denied(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        with self.assertRaises(ValueError):
            accept_result(persisted=self.state(baseline="new"), plan=plan, result_payload=self.result(plan))

    def test_stale_lifecycle_state_is_denied(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        with self.assertRaises(ValueError):
            accept_result(persisted=self.state(State.REPAIRING), plan=plan, result_payload=self.result(plan))

    def test_physical_stop_maps_to_hardware_blocker(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        accepted = accept_result(
            persisted=state, plan=plan, result_payload=self.result(plan, stopReason="PHYSICAL_ACTION_REQUIRED")
        )
        self.assertEqual(accepted.state, State.BLOCKED_HARDWARE)

    def test_secret_stop_maps_to_secret_blocker(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        accepted = accept_result(
            persisted=state, plan=plan, result_payload=self.result(plan, stopReason="SECRET_REQUIRED")
        )
        self.assertEqual(accepted.state, State.BLOCKED_SECRET)

    def test_product_stop_maps_to_product_blocker(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        accepted = accept_result(
            persisted=state, plan=plan, result_payload=self.result(plan, stopReason="PRODUCT_DECISION_REQUIRED")
        )
        self.assertEqual(accepted.state, State.BLOCKED_PRODUCT)

    def test_merge_state_cannot_invoke_executor(self):
        with self.assertRaises(ValueError):
            prepare_invocation(persisted=self.state(State.MERGING), objective="merge")

    def test_executor_cannot_return_merge_output(self):
        state = self.state()
        plan = prepare_invocation(persisted=state, objective="bounded work")
        with self.assertRaises(ValueError):
            accept_result(persisted=state, plan=plan, result_payload=self.result(plan, outputType="merge"))


if __name__ == "__main__":
    unittest.main()
