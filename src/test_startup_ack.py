import unittest
from startup_ack import pending_ack, startup_verdict


class Tests(unittest.TestCase):
    def ack(self):
        return {'status': 'ok', 'token': 'token-123', 'version': '2.0.12'}

    def test_accepts_exact_ack(self):
        self.assertTrue(pending_ack(self.ack(), 'token-123', '2.0.12'))
        self.assertEqual(startup_verdict(self.ack(), 'token-123', '2.0.12', True, False), 'accept')

    def test_rejects_missing_or_extra_fields(self):
        for key in tuple(self.ack()):
            bad = self.ack(); bad.pop(key)
            self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))
        bad = self.ack(); bad['extra'] = True
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))

    def test_rejects_wrong_status_token_or_version(self):
        bad = self.ack(); bad['status'] = 'ready'
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))
        bad = self.ack(); bad['token'] = 'other'
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))
        bad = self.ack(); bad['version'] = '2.0.11'
        self.assertFalse(pending_ack(bad, 'token-123', '2.0.12'))

    def test_rejects_non_dict_or_empty_expected_identity(self):
        self.assertFalse(pending_ack([], 'token-123', '2.0.12'))
        self.assertFalse(pending_ack(self.ack(), '', '2.0.12'))
        self.assertFalse(pending_ack(self.ack(), 'token-123', ''))

    def test_waits_while_process_runs_before_timeout(self):
        self.assertEqual(startup_verdict({}, 'token-123', '2.0.12', True, False), 'wait')

    def test_rolls_back_when_process_exits_without_ack(self):
        self.assertEqual(startup_verdict({}, 'token-123', '2.0.12', False, False), 'rollback-process-exited')

    def test_rolls_back_when_ack_timeout_expires(self):
        self.assertEqual(startup_verdict({}, 'token-123', '2.0.12', True, True), 'rollback-timeout')

    def test_invalid_ack_never_overrides_failure(self):
        bad = self.ack(); bad['token'] = 'other'
        self.assertEqual(startup_verdict(bad, 'token-123', '2.0.12', False, False), 'rollback-process-exited')
        self.assertEqual(startup_verdict(bad, 'token-123', '2.0.12', True, True), 'rollback-timeout')


if __name__ == '__main__':
    unittest.main()
