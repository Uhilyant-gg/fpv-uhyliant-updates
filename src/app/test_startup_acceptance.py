import json
import tempfile
import unittest
from pathlib import Path

from startup_acceptance import startup_acceptance_report, read_startup_acceptance


def events(health_ms=8500):
    return [
        {"stage": "main-entry", "status": "ok", "pid": 7, "elapsedMs": 0},
        {"stage": "restore", "status": "ok", "pid": 7, "elapsedMs": 120},
        {"stage": "launch", "status": "ok", "pid": 7, "elapsedMs": 700},
        {"stage": "discovery", "status": "ok", "pid": 7, "elapsedMs": 900},
        {"stage": "health", "status": "ok", "pid": 7, "elapsedMs": health_ms, "detail": {"health": "unknown"}},
        {"stage": "devices", "status": "ok", "pid": 7, "elapsedMs": health_ms},
        {"stage": "next-action", "status": "ok", "pid": 7, "elapsedMs": health_ms},
    ]


class StartupAcceptanceTests(unittest.TestCase):
    def test_complete_software_journey_is_ready_but_not_physical_evidence(self):
        result = startup_acceptance_report(events())
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["elapsedMs"], 8500)
        self.assertEqual(result["thresholdMs"], 10_000)
        self.assertEqual(result["operation"]["evidence"], "not-collected")

    def test_health_over_ten_seconds_reports_exact_failed_stage(self):
        result = startup_acceptance_report(events(10_001))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stage"], "health")
        self.assertEqual(result["reasonCode"], "startup-health-over-threshold")

    def test_missing_stage_reports_first_missing_stage(self):
        result = startup_acceptance_report(events()[:-1])
        self.assertEqual(result["stage"], "next-action")
        self.assertEqual(result["reasonCode"], "startup-stages-incomplete")

    def test_error_reports_exact_stage(self):
        data = events()
        data[3] = {**data[3], "status": "error"}
        result = startup_acceptance_report(data)
        self.assertEqual(result["stage"], "discovery")
        self.assertEqual(result["reasonCode"], "startup-stage-failed")

    def test_file_reader_uses_latest_invocation_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "startup.jsonl"
            previous = [{**event, "pid": 1} for event in events()]
            current = [{**event, "pid": 2} for event in events()[:-1]]
            path.write_text(
                "\n".join(json.dumps(item) for item in previous + current),
                encoding="utf-8",
            )
            result = read_startup_acceptance(path)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stage"], "next-action")


if __name__ == "__main__":
    unittest.main()
