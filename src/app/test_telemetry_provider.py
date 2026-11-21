import unittest
from PySide6.QtCore import QObject, Signal
from telemetry_provider import MavlinkProvider, MspProvider


class FakeRuntime(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.telemetry = {"connected": True, "armed": False, "batteryVoltage": 15.2, "unexpected": 123}
        self.error = ""


class TelemetryProviderTests(unittest.TestCase):
    def test_normalizes_without_inventing_values(self):
        provider = MavlinkProvider(FakeRuntime())
        telemetry = provider.telemetry
        self.assertEqual(telemetry["provider"], "MAVLink")
        self.assertEqual(telemetry["batteryVoltage"], 15.2)
        self.assertIsNone(telemetry["gpsFix"])
        self.assertNotIn("unexpected", telemetry)
        self.assertTrue(provider.readOnly)
        self.assertTrue(provider.available)

    def test_msp_uses_same_normalized_boundary(self):
        provider = MspProvider(FakeRuntime())
        telemetry = provider.telemetry
        self.assertEqual(telemetry["provider"], "MSP")
        self.assertEqual(telemetry["batteryVoltage"], 15.2)
        self.assertIsNone(telemetry["hdop"])
        self.assertNotIn("unexpected", telemetry)
        self.assertTrue(provider.readOnly)


if __name__ == "__main__":
    unittest.main()
