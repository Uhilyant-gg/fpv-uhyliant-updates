import unittest
from rollback_plan import rollback_preconditions, rolled_back_state


class Tests(unittest.TestCase):
    def test_existing_current_is_replaced_from_rollback(self):
        self.assertEqual(rollback_preconditions(True, True), 'replace-current')

    def test_missing_current_can_restore_rollback(self):
        self.assertEqual(rollback_preconditions(False, True), 'restore-rollback')

    def test_missing_rollback_fails_closed(self):
        self.assertEqual(rollback_preconditions(True, False), 'missing-rollback')
        self.assertEqual(rollback_preconditions(False, False), 'missing-rollback')

    def test_rolled_back_state_clears_pending_and_records_timestamp(self):
        source = {'current':'2.0.12','pendingStartup':True,'packageSha256':'a'*64,'updatedAt':1}
        result = rolled_back_state(source, 42)
        self.assertFalse(result['pendingStartup'])
        self.assertEqual(result['rollbackAt'], 42)
        self.assertTrue(source['pendingStartup'])


if __name__ == '__main__':
    unittest.main()
