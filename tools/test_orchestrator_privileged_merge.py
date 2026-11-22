import unittest
from orchestrator_privileged_merge import authorize
from orchestrator_v2 import Binding

class PrivilegedMergeTests(unittest.TestCase):
    def setUp(self):
        self.binding=Binding("ORCH-S6","base",33,"head")
        self.pr={"number":33,"head":{"sha":"head"},"base":{"sha":"base"}}
        self.checks=[{"name":"verify","status":"completed","conclusion":"success","head_sha":"head"},{"name":"p0-security","status":"completed","conclusion":"success","head_sha":"head"}]
        self.reviews=[{"state":"APPROVED","commit_id":"head","user":{"login":"reviewer"}}]
    def auth(self,**kw):
        a=dict(binding=self.binding,pr=self.pr,checks=self.checks,reviews=self.reviews,required_checks={"verify"},security_checks={"p0-security"},story_id="ORCH-S6",protected_change=False,security_review_for_head=False);a.update(kw);return authorize(**a)
    def test_exact_unprotected_evidence_authorizes(self):self.assertTrue(self.auth().authorized)
    def test_unprotected_solo_change_needs_no_review(self):self.assertTrue(self.auth(reviews=[]).authorized)
    def test_stale_head_denied(self):
        pr={**self.pr,"head":{"sha":"new"}};self.assertEqual(self.auth(pr=pr).reason_code,"stale-execution")
    def test_protected_change_requires_security_review(self):self.assertEqual(self.auth(protected_change=True).reason_code,"security-review-required")
    def test_protected_change_with_exact_security_review_can_continue(self):self.assertTrue(self.auth(protected_change=True,security_review_for_head=True).authorized)
    def test_protected_change_without_review_still_denied(self):self.assertFalse(self.auth(protected_change=True,security_review_for_head=True,reviews=[]).authorized)
    def test_cancelled_required_check_denied(self):
        checks=[dict(self.checks[0],conclusion="cancelled"),self.checks[1]];self.assertFalse(self.auth(checks=checks).authorized)
if __name__=="__main__":unittest.main()
