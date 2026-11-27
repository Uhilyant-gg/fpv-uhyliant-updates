import unittest
from post_flash_verify import verify_post_flash


class PostFlashVerifyTests(unittest.TestCase):
    def setUp(self):
        self.before = {'verified': True, 'platform': 'ssc30kq', 'sensor': 'imx335', 'firmware': 'old'}
        self.profile = {'platform': 'ssc30kq', 'sensor': 'imx335'}

    def test_missing_observation_is_unavailable(self):
        self.assertFalse(verify_post_flash(self.before, {}, self.profile)['ok'])

    def test_verified_matching_observation_passes(self):
        observed = {
            'verified': True,
            'platform': 'ssc30kq',
            'sensor': 'imx335',
            'firmware': 'new',
            'evidence': ['Majestic /api/v1/config.json'],
        }
        self.assertTrue(verify_post_flash(self.before, observed, self.profile)['ok'])

    def test_wrong_sensor_or_firmware_fails(self):
        observed = {
            'verified': True,
            'platform': 'ssc30kq',
            'sensor': 'imx415',
            'firmware': 'old',
            'evidence': ['Majestic /api/v1/config.json'],
        }
        self.assertFalse(verify_post_flash(self.before, observed, self.profile, 'new')['ok'])

    def test_online_upgrade_accepts_new_observed_version_without_inventing_expected_version(self):
        observed = {
            'verified': True,
            'platform': 'ssc30kq',
            'sensor': 'imx335',
            'firmware': 'observed-after-upgrade',
            'evidence': ['OpenIPC status.cgi'],
        }
        r = verify_post_flash(self.before, observed, self.profile, '')
        self.assertTrue(r['ok'])
        self.assertEqual(r['identity']['firmware'], 'observed-after-upgrade')
        self.assertEqual(r['expectedFirmware'], '')

    def test_missing_post_update_firmware_cannot_report_success(self):
        observed = {'verified': True, 'platform': 'ssc30kq', 'sensor': 'imx335', 'evidence': ['OpenIPC status.cgi']}
        r = verify_post_flash(self.before, observed, self.profile, '')
        self.assertFalse(r['ok'])
        self.assertFalse(next(c for c in r['checks'] if c['name'] == 'firmware')['ok'])

    def test_missing_before_identity_cannot_establish_continuity(self):
        observed = {
            'verified': True,
            'platform': 'ssc30kq',
            'sensor': 'imx335',
            'firmware': 'new',
            'evidence': ['OpenIPC status.cgi'],
        }
        self.assertFalse(verify_post_flash({}, observed, self.profile)['ok'])

    def test_partial_before_identity_cannot_establish_continuity(self):
        observed = {
            'verified': True,
            'platform': 'ssc30kq',
            'sensor': 'imx335',
            'firmware': 'new',
            'evidence': ['OpenIPC status.cgi'],
        }
        for before in ({'platform': 'ssc30kq'}, {'sensor': 'imx335'}):
            r = verify_post_flash(before, observed, self.profile)
            self.assertFalse(r['ok'])
            self.assertFalse(next(c for c in r['checks'] if c['name'] == 'identity-continuity')['ok'])


if __name__ == '__main__':
    unittest.main()
