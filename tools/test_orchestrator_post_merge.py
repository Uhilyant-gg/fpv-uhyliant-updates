import tempfile
import unittest
from pathlib import Path

from orchestrator_post_merge import MergeEvidence, build_handoff, save_handoff
from orchestrator_state import PersistedState
from orchestrator_v2 import State


class PostMergeHandoffTests(unittest.TestCase):
    def setUp(self):
        self.state = PersistedState(1, State.UPDATING_STATE, "ORCH-S6", "base", 33, "head", 0, 3)
        self.evidence = MergeEvidence(33, True, "head", "merge")

    def test_exact_merge_creates_handoff(self):
        result = build_handoff(self.state, self.evidence, "ORCH-S7")
        self.assertEqual(result.completed_state, "COMPLETE")
        self.assertEqual(result.next_state, "READY")
        self.assertEqual(result.next_story_id, "ORCH-S7")
        self.assertEqual(result.next_baseline_sha, "merge")

    def test_changed_head_fails_closed(self):
        with self.assertRaises(ValueError):
            build_handoff(self.state, MergeEvidence(33, True, "changed", "merge"), "ORCH-S7")

    def test_wrong_pr_fails_closed(self):
        with self.assertRaises(ValueError):
            build_handoff(self.state, MergeEvidence(34, True, "head", "merge"), "ORCH-S7")

    def test_unmerged_pr_fails_closed(self):
        with self.assertRaises(ValueError):
            build_handoff(self.state, MergeEvidence(33, False, "head", "merge"), "ORCH-S7")

    def test_wrong_state_fails_closed(self):
        state = PersistedState(1, State.MERGING, "ORCH-S6", "base", 33, "head", 0, 3)
        with self.assertRaises(ValueError):
            build_handoff(state, self.evidence, "ORCH-S7")

    def test_same_story_fails_closed(self):
        with self.assertRaises(ValueError):
            build_handoff(self.state, self.evidence, "ORCH-S6")

    def test_atomic_save(self):
        result = build_handoff(self.state, self.evidence, "ORCH-S7")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "handoff.json"
            save_handoff(path, result)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
