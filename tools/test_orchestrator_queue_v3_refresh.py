import unittest

from orchestrator_post_merge import MergeEvidence
from orchestrator_queue_v3 import QueueItem, build_queue
from orchestrator_queue_v3_refresh import RefreshObservation, refresh_queue_from_merge


class QueueV3RefreshTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_queue(
            baseline_sha="old-main",
            items=[QueueItem("S1", "Complete S1"), QueueItem("STALE", "Must not auto-promote")],
        )
        self.evidence = MergeEvidence(pr=55, merged=True, merged_head_sha="head-55", merge_commit_sha="new-main")

    def refresh(self, **kwargs):
        values = {
            "plan": self.plan,
            "completed_story_id": "S1",
            "expected_pr": 55,
            "expected_head_sha": "head-55",
            "observation": RefreshObservation("new-main", self.evidence),
            "refreshed_items": [QueueItem("S2", "Freshly planned S2")],
        }
        values.update(kwargs)
        return refresh_queue_from_merge(**values)

    def test_fresh_output_rebases_queue_on_observed_merge_commit(self):
        result = self.refresh()
        self.assertEqual(result.baseline_sha, "new-main")
        self.assertEqual(result.active.story_id, "S2")
        self.assertNotEqual(result.active.story_id, "STALE")

    def test_empty_fresh_output_completes_queue(self):
        self.assertIsNone(self.refresh(refreshed_items=[]))

    def test_observed_main_must_equal_merge_commit(self):
        observation = RefreshObservation("different-main", self.evidence)
        with self.assertRaisesRegex(ValueError, "refresh-main-not-at-merge-commit"):
            self.refresh(observation=observation)

    def test_merged_pr_must_match_expected_binding(self):
        with self.assertRaisesRegex(ValueError, "refresh-merged-pr-mismatch"):
            self.refresh(expected_pr=99)

    def test_merged_head_must_match_expected_binding(self):
        with self.assertRaisesRegex(ValueError, "refresh-merged-head-mismatch"):
            self.refresh(expected_head_sha="different-head")

    def test_completed_story_must_be_active(self):
        with self.assertRaisesRegex(ValueError, "refresh-completed-story-not-active"):
            self.refresh(completed_story_id="S2")


if __name__ == "__main__":
    unittest.main()
