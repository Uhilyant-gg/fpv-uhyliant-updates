import unittest

from orchestrator_control_plane import prepare_invocation
from orchestrator_queue_v3_executor_result import accept_repair_result
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import State


class QueueV3ExecutorResultTests(unittest.TestCase):
    def setUp(self):
        self.persisted = PersistedState(SCHEMA_VERSION, State.REPAIRING, "S1", "base", 60, "head")
        self.plan = prepare_invocation(
            persisted=self.persisted,
            objective="Repair failed CI",
            max_steps=4,
            allowed_outputs=["patch-proposal", "diagnostic-summary"],
        )

    def result(self, **kwargs):
        values = {
            "schemaVersion": 1,
            "requestDigest": self.plan.request["requestDigest"],
            "storyId": "S1",
            "baselineSha": "base",
            "stepsUsed": 2,
            "outputType": "patch-proposal",
            "payload": "bounded patch proposal",
            "stopReason": None,
        }
        values.update(kwargs)
        return values

    def test_valid_patch_result_returns_ci_running_intent(self):
        result = accept_repair_result(persisted=self.persisted, plan=self.plan, result_payload=self.result())
        self.assertTrue(result.ready_for_application)
        self.assertEqual(result.next_state, State.CI_RUNNING)
        self.assertEqual(result.accepted.payload, "bounded patch proposal")

    def test_diagnostic_output_cannot_be_applied_as_repair(self):
        with self.assertRaisesRegex(ValueError, "repair-result-patch-required"):
            accept_repair_result(
                persisted=self.persisted,
                plan=self.plan,
                result_payload=self.result(outputType="diagnostic-summary"),
            )

    def test_stale_result_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "stale executor result"):
            accept_repair_result(
                persisted=self.persisted,
                plan=self.plan,
                result_payload=self.result(baselineSha="old-base"),
            )

    def test_executor_hardware_stop_stays_blocked(self):
        result = accept_repair_result(
            persisted=self.persisted,
            plan=self.plan,
            result_payload=self.result(stopReason="PHYSICAL_ACTION_REQUIRED"),
        )
        self.assertFalse(result.ready_for_application)
        self.assertEqual(result.next_state, State.BLOCKED_HARDWARE)

    def test_persisted_state_must_remain_repairing(self):
        stale = PersistedState(SCHEMA_VERSION, State.CI_FAILED, "S1", "base", 60, "head")
        with self.assertRaisesRegex(ValueError, "repair-result-state-required"):
            accept_repair_result(persisted=stale, plan=self.plan, result_payload=self.result())


if __name__ == "__main__":
    unittest.main()
