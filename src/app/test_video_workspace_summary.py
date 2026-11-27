import unittest
from video_workspace_summary import video_workspace_summary


class VideoWorkspaceSummaryTests(unittest.TestCase):
    def test_missing_workspace_is_unknown(self):
        self.assertEqual(video_workspace_summary(None)["health"], "unknown")

    def test_primary_selection_is_ready_for_primary_only(self):
        result = video_workspace_summary({"primaryId": "main", "secondaryId": "", "pipAvailable": False})
        self.assertTrue(result["primaryReady"])
        self.assertFalse(result["pipReady"])

    def test_pip_requires_distinct_observed_selection(self):
        result = video_workspace_summary({"primaryId": "main", "secondaryId": "sub", "pipAvailable": True})
        self.assertTrue(result["pipReady"])


if __name__ == "__main__":
    unittest.main()
