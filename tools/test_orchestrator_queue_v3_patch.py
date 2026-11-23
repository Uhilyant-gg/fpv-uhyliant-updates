import unittest

from orchestrator_control_plane import AcceptedExecutorOutput
from orchestrator_queue_v3_executor_result import RepairResultDecision
from orchestrator_queue_v3_patch import PatchFile, build_patch_application_plan
from orchestrator_state import PersistedState, SCHEMA_VERSION
from orchestrator_v2 import State


class QueueV3PatchApplicationTests(unittest.TestCase):
    def setUp(self):
        self.persisted = PersistedState(SCHEMA_VERSION, State.REPAIRING, "S1", "base", 61, "head")
        accepted = AcceptedExecutorOutput("EXECUTOR_RESULT_READY", State.REPAIRING, "patch-proposal", "proposal")
        self.decision = RepairResultDecision(accepted, State.CI_RUNNING, True)

    def test_builds_bound_application_plan(self):
        result = build_patch_application_plan(
            decision=self.decision,
            persisted=self.persisted,
            files=[PatchFile("app/example.py", "print('fixed')\n")],
        )
        self.assertEqual(result.story_id, "S1")
        self.assertEqual(result.baseline_sha, "base")
        self.assertEqual(result.expected_head_sha, "head")
        self.assertEqual(result.next_state, State.CI_RUNNING)

    def test_protected_path_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "patch-protected-path-blocked"):
            build_patch_application_plan(
                decision=self.decision,
                persisted=self.persisted,
                files=[PatchFile("PROJECT_STATE.md", "unsafe")],
            )

    def test_duplicate_path_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "patch-duplicate-path"):
            build_patch_application_plan(
                decision=self.decision,
                persisted=self.persisted,
                files=[PatchFile("app/a.py", "a"), PatchFile("app/a.py", "b")],
            )

    def test_nonaccepted_result_is_blocked(self):
        blocked = RepairResultDecision(self.decision.accepted, State.BLOCKED_HARDWARE, False)
        with self.assertRaisesRegex(ValueError, "patch-accepted-result-required"):
            build_patch_application_plan(
                decision=blocked,
                persisted=self.persisted,
                files=[PatchFile("app/a.py", "a")],
            )

    def test_wrong_lifecycle_state_is_blocked(self):
        stale = PersistedState(SCHEMA_VERSION, State.CI_FAILED, "S1", "base", 61, "head")
        with self.assertRaisesRegex(ValueError, "patch-repair-state-required"):
            build_patch_application_plan(
                decision=self.decision,
                persisted=stale,
                files=[PatchFile("app/a.py", "a")],
            )


if __name__ == "__main__":
    unittest.main()
