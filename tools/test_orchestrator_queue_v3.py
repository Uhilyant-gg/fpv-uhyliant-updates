import unittest

from orchestrator_queue_v3 import QueueItem, build_queue, can_continue, refresh_after_merge


class QueueV3Tests(unittest.TestCase):
    def item(self, story):
        return QueueItem(story, f"Complete {story}")

    def test_first_item_is_only_active_item(self):
        plan = build_queue(baseline_sha="base", items=[self.item("E2-S4"), self.item("E2-S5")])
        self.assertEqual(plan.active.story_id, "E2-S4")
        self.assertEqual([item.story_id for item in plan.pending], ["E2-S5"])

    def test_empty_queue_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "queue-empty"):
            build_queue(baseline_sha="base", items=[])

    def test_duplicate_story_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate-queue-story"):
            build_queue(baseline_sha="base", items=[self.item("E2-S4"), self.item("E2-S4")])

    def test_refresh_requires_completed_active_story(self):
        plan = build_queue(baseline_sha="base", items=[self.item("E2-S4")])
        with self.assertRaisesRegex(ValueError, "completed-story-not-active"):
            refresh_after_merge(
                plan, completed_story_id="E2-S5", merge_commit_sha="merge", refreshed_items=[self.item("E2-S6")]
            )

    def test_post_merge_queue_uses_fresh_merge_baseline_and_fresh_order(self):
        plan = build_queue(baseline_sha="base", items=[self.item("E2-S4"), self.item("old-plan")])
        refreshed = refresh_after_merge(
            plan,
            completed_story_id="E2-S4",
            merge_commit_sha="merge",
            refreshed_items=[self.item("E2-S6"), self.item("E3-S1")],
        )
        self.assertEqual(refreshed.baseline_sha, "merge")
        self.assertEqual(refreshed.active.story_id, "E2-S6")
        self.assertEqual([item.story_id for item in refreshed.pending], ["E3-S1"])

    def test_no_fresh_work_completes_queue(self):
        plan = build_queue(baseline_sha="base", items=[self.item("E2-S4")])
        self.assertIsNone(
            refresh_after_merge(plan, completed_story_id="E2-S4", merge_commit_sha="merge", refreshed_items=[])
        )

    def test_human_boundaries_stop_queue(self):
        self.assertFalse(can_continue(blocker_status="PHYSICAL_ACTION_REQUIRED"))
        self.assertFalse(can_continue(blocker_status="SECRET_REQUIRED"))
        self.assertFalse(can_continue(blocker_status="PRODUCT_DECISION_REQUIRED"))
        self.assertFalse(can_continue(blocker_status="AUTOMATION_BLOCKED"))
        self.assertTrue(can_continue(blocker_status=None))

    def test_unknown_blocker_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown-queue-blocker"):
            can_continue(blocker_status="MAYBE")


if __name__ == "__main__":
    unittest.main()
