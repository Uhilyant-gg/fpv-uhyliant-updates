import unittest
from first_run_acceptance import evaluate_first_run, run_first_run_acceptance


class FirstRunAcceptanceTests(unittest.TestCase):
    def test_accepts_ready_operation_with_no_manual_work(self):
        result = evaluate_first_run(
            {
                "stage": "operation",
                "health": "ready",
                "devices": [{"id": "cam-1"}],
                "primaryActions": [],
                "messages": ["Система готова"],
            },
            elapsed_ms=4200,
        )
        self.assertEqual("accepted", result.status)
        self.assertEqual("first-run-accepted", result.reasonCode)
        self.assertEqual(1, result.deviceCount)

    def test_accepts_blocked_state_with_one_recovery_action(self):
        result = evaluate_first_run(
            {
                "stage": "discovery",
                "health": "attention",
                "devices": [],
                "primaryActions": ["find-camera"],
                "messages": ["Камеру поки не знайдено"],
            },
            elapsed_ms=900,
        )
        self.assertEqual("accepted", result.status)
        self.assertEqual("find-camera", result.primaryAction)

    def test_rejects_state_after_ten_second_budget(self):
        result = evaluate_first_run(
            {
                "stage": "health",
                "health": "unknown",
                "primaryActions": ["diagnose"],
            },
            elapsed_ms=10001,
        )
        self.assertEqual("rejected", result.status)
        self.assertEqual("understandable-state-timeout", result.reasonCode)
        self.assertEqual("health", result.stage)

    def test_rejects_manual_configuration_or_terminal(self):
        result = evaluate_first_run(
            {
                "stage": "discovery",
                "health": "attention",
                "primaryActions": ["continue"],
                "manualConfigRequired": True,
            },
            elapsed_ms=100,
        )
        self.assertEqual("manual-configuration-required", result.reasonCode)

    def test_rejects_raw_technical_message(self):
        result = evaluate_first_run(
            {
                "stage": "health",
                "health": "problem",
                "primaryActions": ["retry"],
                "messages": ["RTSP timeout errno 110"],
            },
            elapsed_ms=150,
        )
        self.assertEqual("technical-message-exposed", result.reasonCode)
        self.assertTrue(result.technicalMessageExposed)

    def test_rejects_multiple_primary_actions(self):
        result = evaluate_first_run(
            {
                "stage": "next-action",
                "health": "attention",
                "primaryActions": ["retry", "manual-ip"],
            },
            elapsed_ms=150,
        )
        self.assertEqual("multiple-primary-actions", result.reasonCode)
        self.assertIsNone(result.primaryAction)

    def test_rejects_blocked_state_without_recovery_action(self):
        result = evaluate_first_run({"stage": "discovery", "health": "problem"}, elapsed_ms=150)
        self.assertEqual("recovery-action-missing", result.reasonCode)

    def test_runner_uses_injected_clock_and_emits_machine_result(self):
        ticks = iter((10.0, 10.321))
        result = run_first_run_acceptance(
            lambda: {"stage": "operation", "health": "ready", "devices": []},
            clock=lambda: next(ticks),
        )
        self.assertEqual("accepted", result["status"])
        self.assertEqual(321, result["elapsedMs"])
        self.assertEqual("operation", result["stage"])


if __name__ == "__main__":
    unittest.main()
