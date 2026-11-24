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

    def test_reachability_transition_is_pure(self):
        state = VirtualDeviceState("camera-1")
        result = simulate(state, {"type": "set-reachable", "value": False})
        self.assertTrue(state.reachable)
        self.assertFalse(result["state"]["reachable"])

    def test_unknown_event_fails_closed(self):
        result = simulate(VirtualDeviceState("camera-1"), {"type": "flash-real-device"})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reasonCode"], "unsupported-simulator-event")
        self.assertFalse(result["physicalEvidenceComplete"])


if __name__ == "__main__":
    unittest.main()
