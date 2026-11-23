import unittest
from diagnostic_finding import diagnostic_finding

class DiagnosticFindingTests(unittest.TestCase):
    def test_missing_evidence_stays_unknown(self):
        result = diagnostic_finding(None)
        self.assertEqual(result["state"], "unknown")
        self.assertEqual(result["safeAction"], "diagnose")

    def test_practical_summary_preserves_known_health(self):
        result = diagnostic_finding({"health":"problem","summary":"Video failed.","reasonCode":"video-problem","safeActions":["diagnose"]})
        self.assertEqual(result["state"], "problem")
        self.assertEqual(result["summary"], "Video failed.")
        self.assertEqual(result["safeAction"], "diagnose")

    def test_mutating_action_is_not_forwarded(self):
        result = diagnostic_finding({"health":"attention","safeActions":["fullflash"]})
        self.assertIsNone(result["safeAction"])

if __name__ == "__main__": unittest.main()
