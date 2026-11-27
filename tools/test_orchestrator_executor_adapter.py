import unittest
from orchestrator_executor_adapter import build_request, parse_result


class ExecutorAdapterTests(unittest.TestCase):
    def setUp(self):
        self.request = build_request(
            story_id="ORCH-S9",
            baseline_sha="base",
            state="IMPLEMENTING",
            objective="Implement bounded work",
            max_steps=6,
            allowed_outputs=["patch-proposal", "test-plan"],
        )

    def result(self, **kw):
        data = {
            "schemaVersion": 1,
            "requestDigest": self.request["requestDigest"],
            "storyId": "ORCH-S9",
            "baselineSha": "base",
            "stepsUsed": 3,
            "outputType": "patch-proposal",
            "payload": "proposal",
            "stopReason": None,
        }
        data.update(kw)
        return data

    def test_round_trip_accepts_bound_result(self):
        self.assertEqual(parse_result(self.request, self.result())[1], "EXECUTOR_RESULT_READY")

    def test_request_digest_changes_with_objective(self):
        other = build_request(
            story_id="ORCH-S9",
            baseline_sha="base",
            state="IMPLEMENTING",
            objective="different",
            max_steps=6,
            allowed_outputs=["patch-proposal", "test-plan"],
        )
        self.assertNotEqual(self.request["requestDigest"], other["requestDigest"])

    def test_result_digest_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_result(self.request, self.result(requestDigest="other"))

    def test_unknown_result_field_fails_closed(self):
        result = self.result()
        result["extra"] = True
        with self.assertRaises(ValueError):
            parse_result(self.request, result)

    def test_stale_baseline_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_result(self.request, self.result(baselineSha="old"))

    def test_budget_escape_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_result(self.request, self.result(stepsUsed=7))

    def test_stop_reason_survives_adapter(self):
        self.assertEqual(parse_result(self.request, self.result(stopReason="SECRET_REQUIRED"))[1], "SECRET_REQUIRED")


if __name__ == "__main__":
    unittest.main()
