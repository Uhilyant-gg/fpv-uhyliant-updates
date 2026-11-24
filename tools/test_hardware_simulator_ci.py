import unittest

from hardware_simulator_ci import run_scenarios


class HardwareSimulatorCITests(unittest.TestCase):
    def test_required_scenarios_are_deterministic_and_green(self):
        first = run_scenarios()
        second = run_scenarios()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "passed")
        self.assertTrue(all(item["passed"] for item in first["scenarios"]))

    def test_scenario_ci_never_claims_physical_evidence(self):
        report = run_scenarios()
        self.assertEqual(report["evidenceKind"], "simulation")
        self.assertFalse(report["physicalEvidenceComplete"])


if __name__ == "__main__":
    unittest.main()
