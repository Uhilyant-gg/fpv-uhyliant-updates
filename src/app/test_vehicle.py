import unittest
from PySide6.QtCore import QObject, Signal
from vehicle import VehicleRuntime


class Provider(QObject):
    changed = Signal()

    def __init__(self, telemetry, error=''):
        super().__init__()
        self.telemetry = telemetry
        self.error = error
        self.name = 'MAVLink'


class Video(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.state = 'stopped'
        self.url = ''
        self.attempts = 0
        self.lastEvent = ''
        self.error = ''


class Tests(unittest.TestCase):
    def test_unknown_connected_remains_unknown_in_diagnostics(self):
        v = VehicleRuntime(Provider({'connected': None, 'health': None}), Video())
        self.assertIsNone(v.diagnostics['telemetryConnected'])
        self.assertIsNone(v.diagnostics['telemetryHealth'])
        self.assertEqual(v.health, 'warning')

    def test_explicit_false_connected_is_preserved(self):
        v = VehicleRuntime(Provider({'connected': False, 'health': 'stale'}), Video())
        self.assertIs(v.diagnostics['telemetryConnected'], False)
        self.assertEqual(v.diagnostics['telemetryHealth'], 'stale')

    def test_true_connected_without_errors_can_be_ok(self):
        v = VehicleRuntime(Provider({'connected': True, 'health': 'ok'}), Video())
        self.assertEqual(v.health, 'ok')


if __name__ == '__main__':
    unittest.main()
