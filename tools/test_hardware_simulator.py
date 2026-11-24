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
        self.assertTrue(result["state"]["identity_verified"])

    def test_disconnect_reconnect_requires_fresh_revalidation(self):
        state = VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True)
        disconnected = simulate(state, {"type": "disconnect"})
        self.assertFalse(disconnected["state"]["reachable"])
        self.assertFalse(disconnected["state"]["evidence_fresh"])
        reconnected = simulate(VirtualDeviceState(**disconnected["state"]), {"type": "reconnect"})
        self.assertTrue(reconnected["state"]["reachable"])
        self.assertFalse(reconnected["state"]["evidence_fresh"])
        self.assertEqual(reconnected["status"], "unknown")
        refreshed = simulate(VirtualDeviceState(**reconnected["state"]), {"type": "verify-identity", "verified": True})
        self.assertTrue(refreshed["state"]["evidence_fresh"])

    def test_reboot_lifecycle_requires_revalidation(self):
        state = VirtualDeviceState("camera-1", identity_verified=True, evidence_fresh=True)
        started = simulate(state, {"type": "start-reboot"})
        self.assertTrue(started["state"]["rebooting"])
        down = simulate(VirtualDeviceState(**started["state"]), {"type": "reboot-unreachable"})
        self.assertFalse(down["state"]["reachable"])
        returned = simulate(VirtualDeviceState(**down["state"]), {"type": "reboot-reachable"})
        self.assertTrue(returned["state"]["reachable"])
        self.assertFalse(returned["state"]["rebooting"])
        self.assertFalse(returned["state"]["evidence_fresh"])
        self.assertEqual(returned["reasonCode"], "reboot-revalidation-required")

    def test_reboot_timeout_is_problem_and_synthetic(self):
        state = VirtualDeviceState("camera-1", rebooting=True, evidence_fresh=False)
        result = simulate(state, {"type": "reboot-timeout"})
        self.assertEqual(result["status"], "problem")
        self.assertEqual(result["reasonCode"], "reboot-timeout-simulated")
        self.assertEqual(result["evidenceKind"], "simulation")
        self.assertFalse(result["physicalEvidenceComplete"])

    def test_identity_cannot_refresh_while_unreachable(self):
        result = simulate(VirtualDeviceState("camera-1", reachable=False), {"type": "verify-identity", "verified": True})
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["state"]["evidence_fresh"])

    def test_unknown_event_fails_closed(self):
        result = simulate(VirtualDeviceState("camera-1"), {"type": "flash-real-device"})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasonCode"], "unsupported-simulator-event")
        self.assertFalse(result["physicalEvidenceComplete"])


if __name__ == "__main__":
    unittest.main()
