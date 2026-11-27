import unittest
from network_remediation import classify_network, remediation


class Tests(unittest.TestCase):
    def test_unknown_network_requests_read_only_refresh(self):
        r = classify_network({'network': {'state': 'unavailable'}})
        self.assertEqual(r['state'], 'unknown')
        self.assertEqual(r['action'], 'refresh-network')

    def test_degraded_connection_prefers_reprobe_for_known_device(self):
        r = classify_network({'network': {'state': 'degraded'}}, device_present=True)
        self.assertEqual(r['state'], 'attention')
        self.assertEqual(r['action'], 'reprobe-device')

    def test_video_failure_on_ready_network_prefers_video_reconnect(self):
        r = classify_network({'network': {'state': 'ready'}}, 'stalled', True)
        self.assertEqual(r['action'], 'reconnect-video')

    def test_ready_network_has_no_fix(self):
        r = classify_network({'network': {'state': 'ready'}}, 'playing', True)
        self.assertEqual(r['state'], 'ready')
        self.assertIsNone(r['action'])

    def test_only_allowlisted_remediation_is_exposed(self):
        self.assertFalse(remediation('refresh-network')['mutating'])
        self.assertIsNone(remediation('shell'))
        self.assertIsNone(remediation('set-static-ip'))


if __name__ == '__main__':
    unittest.main()
