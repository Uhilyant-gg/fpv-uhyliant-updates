import unittest
from startup_ack import pending_ack


class Tests(unittest.TestCase):
    def ack(self):
        return {'status': 'ok', 'token': 'token-123', 'version': '2.0.12'}

    def test_accepts_exact_ack(self):
        self.assertTrue(pending_ack(self.ack(), 'token-123', '2.0.12'))

    def test_rejects_missing_or_extra_fields(self):
        for key in tuple(self.ack()):
            bad = self.ack()
            bad.pop(key)
            self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))
        bad = self.ack()
        bad['extra'] = True
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))

    def test_rejects_wrong_status_token_or_version(self):
        bad = self.ack()
        bad['status'] = 'ready'
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))
        bad = self.ack()
        bad['token'] = 'other'
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))
        bad = self.ack()
        bad['version'] = '2.0.11'
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))

    def test_rejects_non_dict_or_empty_expected_identity(self):
        self.assertFalse(pending_ack([], 'token-123', '2.0.12'))
        self.assertFalse(pending_ack(self.ack(), '', '2.0.12'))
        self.assertFalse(pending_ack(self.ack(), 'token-123', ''))


if __name__ == '__main__':
    unittest.main()
