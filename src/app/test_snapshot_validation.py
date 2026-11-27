import unittest
from snapshot_validation import validate_snapshot


def base():
    return {
        'devices': [
            {
                'id': 'cam',
                'name': 'Camera',
                'type': 'Camera',
                'host': '192.168.1.40',
                'port': 80,
                'connection': 'Network',
                'notes': '',
            }
        ],
        'streams': [
            {
                'id': 'main',
                'device_id': 'cam',
                'name': 'Main',
                'kind': 'main',
                'protocol': 'rtsp',
                'port': 554,
                'path': '/stream=0',
                'video_profile_id': 'balanced',
                'enabled': True,
            }
        ],
        'videoProfiles': [
            {
                'id': 'balanced',
                'name': 'Balanced',
                'codec': 'h264',
                'width': None,
                'height': None,
                'fps': 30,
                'bitrate_kbps': None,
                'latency_mode': 'balanced',
                'notes': '',
            }
        ],
        'openipcIdentities': [
            {
                'device_id': 'cam',
                'verified': True,
                'platform': 'ssc30kq',
                'soc': '',
                'sensor': 'imx335',
                'firmware': '',
                'majestic': '',
                'evidence': ['Majestic'],
            }
        ],
        'activeDeviceId': 'cam',
    }


class Tests(unittest.TestCase):
    def test_valid_snapshot(self):
        self.assertTrue(validate_snapshot(base()))

    def test_rejects_unknown_fields(self):
        v = base()
        v['devices'][0]['secret'] = 'x'
        self.assertFalse(validate_snapshot(v))

    def test_rejects_duplicate_device_host_port(self):
        v = base()
        v['devices'].append({**v['devices'][0], 'id': 'cam2'})
        self.assertFalse(validate_snapshot(v))

    def test_rejects_dangling_profile(self):
        v = base()
        v['streams'][0]['video_profile_id'] = 'missing'
        self.assertFalse(validate_snapshot(v))

    def test_rejects_wrong_numeric_types(self):
        v = base()
        v['devices'][0]['port'] = '80'
        self.assertFalse(validate_snapshot(v))

    def test_rejects_unverified_identity(self):
        v = base()
        v['openipcIdentities'][0]['verified'] = False
        self.assertFalse(validate_snapshot(v))


if __name__ == '__main__':
    unittest.main()
