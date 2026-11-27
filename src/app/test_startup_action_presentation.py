import unittest
from startup_action_presentation import startup_action_presentation


class Tests(unittest.TestCase):
    def test_missing_hidden(self):
        self.assertFalse(startup_action_presentation(None)['visible'])

    def test_known_action_presented(self):
        r = startup_action_presentation({'action': 'connect-camera', 'reasonCode': 'verified'})
        self.assertTrue(r['visible'])
        self.assertEqual(r['label'], 'Підключити камеру')

    def test_unknown_action_not_exposed(self):
        r = startup_action_presentation({'action': 'flash-camera'})
        self.assertFalse(r['visible'])
        self.assertIsNone(r['action'])

    def test_presentation_preserves_reason(self):
        self.assertEqual(
            startup_action_presentation({'action': 'show-video', 'reasonCode': 'stream-ready'})['reasonCode'],
            'stream-ready',
        )


if __name__ == '__main__':
    unittest.main()
