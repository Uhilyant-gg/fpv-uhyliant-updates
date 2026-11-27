import unittest

from hardware_simulator import VirtualDeviceState, simulate


class HardwareSimulatorTests(unittest.TestCase):
    def test_observe_is_deterministic(self):
        state = VirtualDeviceState("camera-1", firmware_version="test")
        self.assertEqual(simulate(state, {"type": "observe"}), simulate(state, {"type": "observe"}))

    def test_simulation_never_claims_physical_evidence(self):
        result = simulate(VirtualDeviceState("camera-1"), {"type": "verify-identity", "verified": True})
        self.assertEqual(result["evidenceKind"], "simulation")
        self.assertFalse(result["physicalEvidenceComplete"])

    def test_disconnect_reconnect_requires_fresh_revalidation(self):
        state = VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True)
        disconnected = simulate(state, {"type": "disconnect"})
        reconnected = simulate(VirtualDeviceState(**disconnected["state"]), {"type": "reconnect"})
        self.assertTrue(reconnected["state"]["reachable"])
        self.assertFalse(reconnected["state"]["evidence_fresh"])
        refreshed = simulate(VirtualDeviceState(**reconnected["state"]), {"type": "verify-identity", "verified": True})
        self.assertTrue(refreshed["state"]["evidence_fresh"])

    def test_reboot_lifecycle_requires_revalidation(self):
        state = VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True)
        started = simulate(state, {"type": "start-reboot"})
        down = simulate(VirtualDeviceState(**started["state"]), {"type": "reboot-unreachable"})
        returned = simulate(VirtualDeviceState(**down["state"]), {"type": "reboot-reachable"})
        self.assertTrue(returned["state"]["reachable"])
        self.assertFalse(returned["state"]["evidence_fresh"])

    def test_identity_faults_invalidate_old_evidence(self):
        initial = VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True)
        for fault, status in (("identity-unavailable", "unknown"), ("identity-stale", "unknown"), ("identity-mismatch", "problem")):
            result = simulate(initial, {"type": fault})
            self.assertEqual(result["status"], status)
            self.assertFalse(result["state"]["evidence_fresh"])
            self.assertFalse(result["physicalEvidenceComplete"])

    def test_identity_fault_only_recovers_after_revalidation(self):
        faulted = simulate(VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True), {"type": "identity-mismatch"})
        observed = simulate(VirtualDeviceState(**faulted["state"]), {"type": "observe"})
        self.assertFalse(observed["state"]["evidence_fresh"])
        refreshed = simulate(VirtualDeviceState(**observed["state"]), {"type": "verify-identity", "verified": True})
        self.assertTrue(refreshed["state"]["identity_verified"])
        self.assertTrue(refreshed["state"]["evidence_fresh"])

    def test_update_failure_is_deterministic(self):
        state = VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True)
        started_a = simulate(state, {"type": "start-update"})
        started_b = simulate(state, {"type": "start-update"})
        self.assertEqual(started_a, started_b)
        failed_a = simulate(VirtualDeviceState(**started_a["state"]), {"type": "fail-update"})
        failed_b = simulate(VirtualDeviceState(**started_b["state"]), {"type": "fail-update"})
        self.assertEqual(failed_a, failed_b)
        self.assertEqual(failed_a["status"], "problem")
        self.assertTrue(failed_a["state"]["update_failed"])

    def test_interrupted_update_fails_closed(self):
        started = simulate(VirtualDeviceState("camera-1"), {"type": "start-update"})
        result = simulate(VirtualDeviceState(**started["state"]), {"type": "interrupt-update"})
        self.assertEqual(result["reasonCode"], "update-interrupted-simulated")
        self.assertTrue(result["state"]["update_failed"])
        self.assertFalse(result["state"]["evidence_fresh"])

    def test_invalid_update_while_unreachable(self):
        result = simulate(VirtualDeviceState("camera-1", reachable=False), {"type": "start-update"})
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["state"]["update_active"])

    def test_identity_verification_during_reboot_fails_closed(self):
        result = simulate(VirtualDeviceState("camera-1", rebooting=True), {"type": "verify-identity", "verified": True})
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["state"]["evidence_fresh"])

    def test_complete_update_without_transaction_fails_closed(self):
        result = simulate(VirtualDeviceState("camera-1"), {"type": "complete-update", "firmwareVersion": "new"})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasonCode"], "update-completion-without-transaction")

    def test_unknown_event_fails_closed(self):
        result = simulate(VirtualDeviceState("camera-1"), {"type": "flash-real-device"})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasonCode"], "unsupported-simulator-event")
        self.assertFalse(result["physicalEvidenceComplete"])


if __name__ == "__main__":
    unittest.main()
