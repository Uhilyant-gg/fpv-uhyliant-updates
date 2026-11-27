import unittest
from discovery_startup_summary import discovery_startup_summary


class Tests(unittest.TestCase):
    def test_single_verified_candidate_is_connectable(self):
        r = discovery_startup_summary([], [{'host': '192.168.1.5', 'openipc': True, 'identityVerified': True}])
        self.assertEqual(r['action'], 'connect-camera')
        self.assertEqual(r['host'], '192.168.1.5')

    def test_saved_match_is_only_metadata(self):
        r = discovery_startup_summary(
            [{'host': '192.168.1.5'}], [{'host': '192.168.1.5', 'openipc': True, 'identityVerified': True}]
        )
        self.assertTrue(r['restored'])

    def test_multiple_verified_candidates_fail_closed(self):
        r = discovery_startup_summary(
            [],
            [
                {'host': '192.168.1.5', 'openipc': True, 'identityVerified': True},
                {'host': '192.168.1.6', 'openipc': True, 'identityVerified': True},
            ],
        )
        self.assertIsNone(r['action'])
        self.assertEqual(r['health'], 'attention')

    def test_unverified_candidate_never_becomes_ready(self):
        r = discovery_startup_summary([], [{'host': '192.168.1.5', 'openipc': True, 'identityVerified': False}])
        self.assertEqual(r['health'], 'unknown')
        self.assertEqual(r['action'], 'find-camera')


if __name__ == '__main__':
    unittest.main()
