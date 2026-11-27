import unittest
from backup_status_summary import backup_status_summary

class BackupStatusSummaryTests(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(backup_status_summary(None)["health"],"unknown")

    def test_verified_plan_requires_confirmation(self):
        result=backup_status_summary({"ready":True,"manifest":{"execution":"explicit-confirmation-required"}})
        self.assertEqual(result["health"],"attention");self.assertTrue(result["restoreReady"])

    def test_completed_restore_is_ready_but_not_pending(self):
        result=backup_status_summary({"ready":True,"manifest":{"restored":True}})
        self.assertEqual(result["health"],"ready");self.assertFalse(result["restoreReady"])

if __name__ == "__main__": unittest.main()
