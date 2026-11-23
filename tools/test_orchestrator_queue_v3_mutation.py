import unittest

from orchestrator_queue_v3_mutation import prepare_mutation
from orchestrator_queue_v3_patch import PatchApplicationPlan, PatchFile
from orchestrator_v2 import State


class QueueV3MutationGateTests(unittest.TestCase):
    def setUp(self):
        self.plan = PatchApplicationPlan(
            story_id="S1",
            baseline_sha="base",
            expected_head_sha="head",
            files=(PatchFile("app/example.py", "fixed\n"),),
            next_state=State.CI_RUNNING,
        )

    def test_exact_head_builds_branch_mutation(self):
        result = prepare_mutation(plan=self.plan, branch="copilot/repair-s1", observed_head_sha="head")
        self.assertEqual(result.branch, "copilot/repair-s1")
        self.assertEqual(result.expected_head_sha, "head")
        self.assertEqual(result.files, (("app/example.py", "fixed\n"),))
        self.assertEqual(result.next_state, State.CI_RUNNING)

    def test_direct_main_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "mutation-direct-main-blocked"):
            prepare_mutation(plan=self.plan, branch="main", observed_head_sha="head")

    def test_stale_head_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "mutation-stale-head"):
            prepare_mutation(plan=self.plan, branch="copilot/repair-s1", observed_head_sha="new-head")

    def test_missing_observed_head_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "mutation-observed-head-required"):
            prepare_mutation(plan=self.plan, branch="copilot/repair-s1", observed_head_sha=" ")

    def test_non_ci_running_plan_is_blocked(self):
        bad = PatchApplicationPlan("S1", "base", "head", self.plan.files, State.REPAIRING)
        with self.assertRaisesRegex(ValueError, "mutation-ci-rerun-required"):
            prepare_mutation(plan=bad, branch="copilot/repair-s1", observed_head_sha="head")


if __name__ == "__main__":
    unittest.main()
