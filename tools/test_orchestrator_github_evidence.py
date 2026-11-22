import unittest
from orchestrator_github_evidence import collect
from orchestrator_repair import decide_repair
from orchestrator_v2 import Binding,State

class EvidenceCollectorTests(unittest.TestCase):
    def setUp(self):
        self.pr={"number":31,"head":{"sha":"head"},"base":{"sha":"base"}}
        self.checks=[{"name":"verify","status":"completed","conclusion":"success","head_sha":"head"},{"name":"p0-security","status":"completed","conclusion":"success","head_sha":"head"}]
        self.reviews=[{"state":"APPROVED","commit_id":"head","user":{"login":"reviewer"}}]
    def collect(self,**overrides):
        args=dict(pr=self.pr,checks=self.checks,reviews=self.reviews,required_checks={"verify"},security_checks={"p0-security"},story_id="ORCH-S4"); args.update(overrides); return collect(**args)
    def test_exact_green_evidence(self):
        e,reason=self.collect(); self.assertEqual(reason,"ready"); self.assertTrue(e.required_ci_green and e.security_green and e.review_approved); self.assertEqual(e.tested_sha,"head")
    def test_missing_required_check_fails_closed(self):
        e,reason=self.collect(required_checks={"verify","missing"}); self.assertFalse(e.required_ci_green); self.assertEqual(reason,"required-check-missing")
    def test_stale_tested_sha_fails_closed(self):
        checks=[dict(x,head_sha="old") if x["name"]=="verify" else x for x in self.checks]; e,reason=self.collect(checks=checks); self.assertEqual(reason,"tested-sha-stale")
    def test_review_must_match_head(self):
        reviews=[{"state":"APPROVED","commit_id":"old","user":{"login":"reviewer"}}]; e,reason=self.collect(reviews=reviews); self.assertFalse(e.review_approved); self.assertEqual(reason,"review-not-approved-for-head")
    def test_duplicate_required_check_is_ambiguous(self):
        e,reason=self.collect(checks=self.checks+[self.checks[0]]); self.assertEqual(reason,"duplicate-required-check")
    def test_bounded_repair_only_for_bound_failed_ci(self):
        failed=[dict(self.checks[0],conclusion="failure"),self.checks[1]]; e,_=self.collect(checks=failed)
        b=Binding("ORCH-S4","base",31,"head"); d=decide_repair(b,e,ci_status="failed",attempts=0,max_attempts=2); self.assertEqual(d.state,State.REPAIRING); self.assertTrue(d.invoke_ai); self.assertEqual(d.attempts,1)
        d=decide_repair(b,e,ci_status="failed",attempts=2,max_attempts=2); self.assertEqual(d.state,State.BLOCKED_AUTOMATION); self.assertFalse(d.invoke_ai)
    def test_repair_rejects_stale_execution(self):
        failed=[dict(self.checks[0],conclusion="failure"),self.checks[1]]; e,_=self.collect(checks=failed)
        d=decide_repair(Binding("ORCH-S4","base",31,"old"),e,ci_status="failed",attempts=0,max_attempts=2); self.assertEqual(d.state,State.STATE_INCONSISTENT); self.assertFalse(d.invoke_ai)
if __name__=="__main__":unittest.main()
