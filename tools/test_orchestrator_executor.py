import unittest
from orchestrator_executor import ExecutorRequest,ExecutorResult,validate_result
from orchestrator_v2 import State

class ExecutorContractTests(unittest.TestCase):
    def setUp(self):
        self.request=ExecutorRequest("ORCH-S8","base",State.IMPLEMENTING,"Implement bounded batch",4,("patch-proposal","test-plan"))
    def result(self,**kw):
        data=dict(story_id="ORCH-S8",baseline_sha="base",steps_used=2,output_type="patch-proposal",payload="proposal",stop_reason=None);data.update(kw);return ExecutorResult(**data)
    def test_bound_result_is_accepted(self):self.assertEqual(validate_result(self.request,self.result()),"EXECUTOR_RESULT_READY")
    def test_stale_story_is_denied(self):
        with self.assertRaises(ValueError):validate_result(self.request,self.result(story_id="other"))
    def test_stale_baseline_is_denied(self):
        with self.assertRaises(ValueError):validate_result(self.request,self.result(baseline_sha="other"))
    def test_step_budget_is_enforced(self):
        with self.assertRaises(ValueError):validate_result(self.request,self.result(steps_used=5))
    def test_unapproved_output_is_denied(self):
        with self.assertRaises(ValueError):validate_result(self.request,self.result(output_type="merge"))
    def test_physical_stop_is_preserved(self):self.assertEqual(validate_result(self.request,self.result(stop_reason="PHYSICAL_ACTION_REQUIRED")),"PHYSICAL_ACTION_REQUIRED")
    def test_secret_stop_is_preserved(self):self.assertEqual(validate_result(self.request,self.result(stop_reason="SECRET_REQUIRED")),"SECRET_REQUIRED")
    def test_product_stop_is_preserved(self):self.assertEqual(validate_result(self.request,self.result(stop_reason="PRODUCT_DECISION_REQUIRED")),"PRODUCT_DECISION_REQUIRED")
    def test_executor_cannot_run_in_merge_state(self):
        request=ExecutorRequest("ORCH-S8","base",State.MERGING,"merge",1,("patch-proposal",))
        with self.assertRaises(ValueError):request.validate()
if __name__=="__main__":unittest.main()
