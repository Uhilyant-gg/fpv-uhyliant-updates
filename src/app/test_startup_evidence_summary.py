import unittest
from startup_evidence_summary import startup_evidence_summary


class StartupEvidenceSummaryTests(unittest.TestCase):
    def test_missing_evidence_is_unknown(self):
        self.assertEqual(startup_evidence_summary(None)["health"], "unknown")

    def test_intermediate_success_is_not_ready(self):
        self.assertEqual(
            startup_evidence_summary({"stage": "qml-engine-complete", "status": "ok"})["health"], "attention"
        )

    def test_terminal_probe_success_can_be_ready(self):
        self.assertEqual(startup_evidence_summary({"stage": "probe-complete", "status": "ok"})["health"], "ready")

    def test_error_is_problem(self):
        self.assertEqual(startup_evidence_summary({"stage": "pyside-qml", "status": "error"})["health"], "problem")


if __name__ == "__main__":
    unittest.main()
