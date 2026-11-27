import unittest
from stream_continuity import stream_continuity


class Tests(unittest.TestCase):
    def test_missing_evidence_unknown(self):
        self.assertEqual(stream_continuity(None, None)['health'], 'unknown')

    def test_loss_requests_reconnect(self):
        self.assertEqual(stream_continuity({'primaryId': 'main'}, {'primaryId': ''})['action'], 'reconnect-video')

    def test_change_is_attention(self):
        self.assertEqual(stream_continuity({'primaryId': 'main'}, {'primaryId': 'sub'})['health'], 'attention')

    def test_same_primary_is_ready(self):
        self.assertEqual(stream_continuity({'primaryId': 'main'}, {'primaryId': 'main'})['health'], 'ready')


if __name__ == '__main__':
    unittest.main()
