import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import first_run_acceptance


class FirstRunAcceptanceCliTests(unittest.TestCase):
    def test_cli_returns_zero_for_accepted_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            path.write_text(
                json.dumps(
                    {
                        "stage": "operation",
                        "health": "ready",
                        "devices": [],
                        "primaryActions": [],
                        "messages": ["Готово"],
                    }
                ),
                encoding="utf-8",
            )
            with patch("builtins.print") as output:
                code = first_run_acceptance.main([str(path), "--elapsed-ms", "500"])
            self.assertEqual(0, code)
            payload = json.loads(output.call_args.args[0])
            self.assertEqual("accepted", payload["status"])

    def test_cli_returns_one_and_exact_failed_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            path.write_text(
                json.dumps(
                    {
                        "stage": "health",
                        "health": "problem",
                        "primaryActions": ["diagnose"],
                    }
                ),
                encoding="utf-8",
            )
            with patch("builtins.print") as output:
                code = first_run_acceptance.main([str(path), "--elapsed-ms", "11000"])
            self.assertEqual(1, code)
            payload = json.loads(output.call_args.args[0])
            self.assertEqual("health", payload["stage"])
            self.assertEqual("understandable-state-timeout", payload["reasonCode"])


if __name__ == "__main__":
    unittest.main()
