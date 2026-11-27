import unittest
from windows_startup_readiness import REQUIRED, windows_startup_readiness


class Tests(unittest.TestCase):
    def test_empty_evidence_unknown(self):
        self.assertEqual(windows_startup_readiness([])['health'], 'unknown')

    def test_error_is_problem(self):
        self.assertEqual(windows_startup_readiness([{'stage': 'pyside-qml', 'status': 'error'}])['health'], 'problem')

    def test_all_required_complete_ready(self):
        events = [{'stage': x + '-complete', 'status': 'ok'} for x in REQUIRED]
        self.assertEqual(windows_startup_readiness(events)['health'], 'ready')

    def test_partial_lists_missing(self):
        r = windows_startup_readiness([{'stage': 'python-runtime-complete', 'status': 'ok'}])
        self.assertIn('pyside-qml', r['missing'])


if __name__ == '__main__':
    unittest.main()
