import unittest
from startup_journey import startup_journey


class Tests(unittest.TestCase):
    def test_missing_starts_unknown_discovery(self):
        self.assertEqual(startup_journey(None)['action'], 'find-camera')

    def test_restore_has_bounded_step(self):
        self.assertEqual(
            startup_journey(
                {'health': 'unknown', 'stage': 'restore', 'action': 'restore-camera', 'reasonCode': 'saved'}
            )['step'],
            2,
        )

    def test_operate_requires_ready(self):
        self.assertEqual(startup_journey({'health': 'attention', 'stage': 'operate'})['stage'], 'video')

    def test_ready_operate_is_final(self):
        r = startup_journey({'health': 'ready', 'stage': 'operate', 'action': 'show-video', 'reasonCode': 'ready'})
        self.assertEqual(r['step'], r['total'])
        self.assertEqual(r['health'], 'ready')


if __name__ == '__main__':
    unittest.main()
