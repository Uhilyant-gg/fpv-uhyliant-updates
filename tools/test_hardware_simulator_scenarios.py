import unittest

from hardware_simulator import VirtualDeviceState, simulate
from hardware_simulator_scenarios import replay, retry_update, select_device, validate_state


class HardwareSimulatorScenarioTests(unittest.TestCase):
    def assert_synthetic(self, result):
        self.assertEqual(result["evidenceKind"], "simulation")
        self.assertFalse(result["physicalEvidenceComplete"])

    def test_revalidation_after_fault_restores_freshness(self):
        fault = simulate(
            VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True), {"type": "identity-stale"}
        )
        recovered = simulate(VirtualDeviceState(**fault["state"]), {"type": "verify-identity", "verified": True})
        self.assertTrue(recovered["state"]["evidence_fresh"])
        self.assert_synthetic(recovered)

    def test_retry_after_update_failure(self):
        failed = VirtualDeviceState("camera-1", update_failed=True)
        result = retry_update(failed, retry_count=0, retry_budget=2)
        self.assertTrue(result["state"]["update_active"])
        self.assertFalse(result["state"]["update_failed"])
        self.assert_synthetic(result)

    def test_retry_invalid_state_fails_closed(self):
        result = retry_update(VirtualDeviceState("camera-1"), 0, 2)
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasonCode"], "update-retry-invalid-state")

    def test_retry_budget_exhaustion_is_deterministic_problem(self):
        state = VirtualDeviceState("camera-1", update_failed=True)
        a = retry_update(state, 2, 2)
        b = retry_update(state, 2, 2)
        self.assertEqual(a, b)
        self.assertEqual(a["status"], "problem")
        self.assertEqual(a["reasonCode"], "update-retry-budget-exhausted")

    def test_device_selection_zero_one_many(self):
        none = select_device([])
        one = select_device([VirtualDeviceState("camera-1")])
        many = select_device([VirtualDeviceState("camera-1"), VirtualDeviceState("camera-2")])
        self.assertIsNone(none["selectedDeviceId"])
        self.assertEqual(one["selectedDeviceId"], "camera-1")
        self.assertIsNone(many["selectedDeviceId"])
        self.assertEqual(many["reasonCode"], "simulated-device-ambiguous")

    def test_malformed_events_fail_closed(self):
        result = replay(VirtualDeviceState("camera-1"), [{"value": True}])
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasonCode"], "malformed-scenario-event")
        self.assertEqual(result["stoppedAt"], 0)

    def test_malformed_and_contradictory_state_fail_closed(self):
        malformed = validate_state({"device_id": "camera-1"})
        contradictory = validate_state(VirtualDeviceState("camera-1", update_active=True, update_failed=True))
        self.assertEqual(malformed["reasonCode"], "malformed-virtual-state")
        self.assertEqual(contradictory["reasonCode"], "contradictory-virtual-state")
        self.assertNotEqual(contradictory["status"], "ready")

    def test_scenario_replay_is_deterministic(self):
        initial = VirtualDeviceState("camera-1")
        events = [
            {"type": "verify-identity", "verified": True},
            {"type": "disconnect"},
            {"type": "reconnect"},
            {"type": "verify-identity", "verified": True},
        ]
        self.assertEqual(replay(initial, events), replay(initial, events))
        result = replay(initial, events)
        self.assertEqual(result["reasonCode"], "scenario-complete")
        self.assertTrue(result["state"]["evidence_fresh"])
        self.assert_synthetic(result)

    def test_scenario_stops_on_deterministic_failure(self):
        result = replay(
            VirtualDeviceState("camera-1"), [{"type": "start-update"}, {"type": "fail-update"}, {"type": "observe"}]
        )
        self.assertEqual(result["reasonCode"], "update-failed-simulated")
        self.assertEqual(result["stoppedAt"], 1)
        self.assertEqual(len(result["trace"]), 2)
        self.assert_synthetic(result)

    def test_synthetic_success_never_claims_e0(self):
        result = replay(VirtualDeviceState("camera-1"), [{"type": "verify-identity", "verified": True}])
        self.assertEqual(result["status"], "ready")
        self.assert_synthetic(result)


if __name__ == "__main__":
    unittest.main()
