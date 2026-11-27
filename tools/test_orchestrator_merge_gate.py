import unittest
from orchestrator_merge_gate import evaluate_event, exit_code_for


class MergeAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.event = {"number": 32, "pull_request": {"number": 32, "head": {"sha": "head"}, "base": {"sha": "base"}}}
        self.checks = [
            {"name": "verify", "status": "completed", "conclusion": "success", "head_sha": "head"},
            {"name": "p0-security", "status": "completed", "conclusion": "success", "head_sha": "head"},
        ]
        self.reviews = [{"state": "APPROVED", "commit_id": "head", "user": {"login": "reviewer"}}]

    def run_gate(self, **kw):
        a = dict(
            event=self.event,
            checks=self.checks,
            reviews=self.reviews,
            required_checks={"verify"},
            security_checks={"p0-security"},
            story_id="ORCH-S5",
            expected_head_sha="head",
        )
        a.update(kw)
        return evaluate_event(**a)

    def test_exact_evidence_allows_authority(self):
        self.assertTrue(self.run_gate()["mergeEligible"])

    def test_solo_policy_does_not_require_self_approval(self):
        self.assertTrue(self.run_gate(reviews=[])["mergeEligible"])

    def test_stale_run_denied_before_policy(self):
        self.assertEqual(self.run_gate(expected_head_sha="old")["reasonCode"], "stale-execution")

    def test_failed_security_denied(self):
        checks = [self.checks[0], dict(self.checks[1], conclusion="failure")]
        self.assertFalse(self.run_gate(checks=checks)["mergeEligible"])

    def test_optional_security_scope_allows_ordinary_pr(self):
        result = self.run_gate(checks=[self.checks[0]], security_checks=set())
        self.assertTrue(result["mergeEligible"])
        self.assertEqual(result["reasonCode"], "ready-to-merge")

    def test_protected_scope_still_fails_without_security_check(self):
        result = self.run_gate(checks=[self.checks[0]])
        self.assertFalse(result["mergeEligible"])
        self.assertEqual(result["reasonCode"], "required-check-missing")

    def test_stale_tested_sha_denied(self):
        checks = [dict(self.checks[0], head_sha="old"), self.checks[1]]
        self.assertFalse(self.run_gate(checks=checks)["mergeEligible"])

    def test_running_required_check_is_nonterminal(self):
        checks = [dict(self.checks[0], status="in_progress", conclusion=None), self.checks[1]]
        result = self.run_gate(checks=checks)
        self.assertFalse(result["mergeEligible"])
        self.assertEqual(result["reasonCode"], "required-check-running")
        self.assertEqual(exit_code_for(result), 0)

    def test_failed_check_remains_terminal(self):
        checks = [dict(self.checks[0], conclusion="failure"), self.checks[1]]
        self.assertEqual(exit_code_for(self.run_gate(checks=checks)), 3)


if __name__ == "__main__":
    unittest.main()
