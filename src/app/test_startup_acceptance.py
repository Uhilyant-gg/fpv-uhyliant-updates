import json
import tempfile
import unittest
from pathlib import Path

from startup_acceptance import startup_acceptance_report, read_startup_acceptance


def events(health_ms=8500):
    return [
        {"stage": "main-entry", "status": "ok", "pid": 7, "elapsedMs": 0},
        {"stage": "launch", "status": "ok", "pid": 7, "elapsedMs": 50},
        {"stage": "restore", "status": "ok", "pid": 7, "elapsedMs": 120},
        {"stage": "discovery", "status": "ok", "pid": 7, "elapsedMs": 700},
        {"stage": "window-visible", "status": "ok", "pid": 7, "elapsedMs": 900},
        {"stage": "health", "status": "ok", "pid": 7, "elapsedMs": health_ms, "detail": {"health": "unknown", "summary": "Стан перевіряється"}},
        {"stage": "devices", "status": "ok", "pid": 7, "elapsedMs": health_ms, "detail": {"devices": []}},
        {"stage": "next-action", "status": "ok", "pid": 7, "elapsedMs": health_ms, "detail": {"available": True, "action": "find-camera"}},
    ]


class StartupAcceptanceTests(unittest.TestCase):
    def test_complete_software_journey_uses_shared_contract_without_claiming_physical_evidence(self):
        result = startup_acceptance_report(events())
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["elapsedMs"], 8500)
        self.assertEqual(result["thresholdMs"], 10_000)
        self.assertEqual(result["reasonCode"], "first-run-accepted")
        self.assertEqual(result["physicalOperationEvidence"], "not-collected")

    def test_health_over_ten_seconds_reports_exact_failed_stage(self):
        result = startup_acceptance_report(events(10_001))
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["stage"], "health")
        self.assertEqual(result["reasonCode"], "understandable-state-timeout")

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

    def test_network_free_packaged_fixture_is_explicit_and_not_physical_evidence(self):
        data = events()
        data[3] = {
            **data[3],
            "detail": {
                "mode": "network-free-packaged-first-run-fixture",
                "networkRequestsSuppressed": True,
                "started": False,
            },
        }
        result = startup_acceptance_report(data)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["evidenceMode"], "network-free-packaged-first-run-fixture")
        self.assertEqual(result["physicalOperationEvidence"], "not-collected")

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
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["stage"], "next-action")


if __name__ == "__main__":
    unittest.main()
