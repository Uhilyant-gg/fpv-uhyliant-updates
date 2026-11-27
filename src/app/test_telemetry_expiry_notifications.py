import unittest

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from crsf_runtime import CRSF_FRAMETYPE_BATTERY_SENSOR, CrsfRuntime
from msp_runtime import MSP_ALTITUDE, MspRuntime
from telemetry_provider import CrsfProvider, MspProvider
from test_crsf_runtime import frame
from test_msp_runtime import response_v1


_app = QCoreApplication.instance() or QCoreApplication([])


class TelemetryExpiryNotificationTests(unittest.TestCase):
    def test_expiry_notifies_provider_without_new_frames(self):
        examples = (
            (
                CrsfRuntime,
                CrsfProvider,
                frame(CRSF_FRAMETYPE_BATTERY_SENSOR, b'\x00\x98\x00\x0c\x00\x00\x01\x4b'),
                'batteryVoltage',
            ),
            (MspRuntime, MspProvider, response_v1(MSP_ALTITUDE, b'\x64\x00\x00\x00'), 'altitude'),
        )
        for runtime_type, provider_type, packet, field in examples:
            with self.subTest(provider=provider_type.__name__):
                now = [0.0]
                runtime = runtime_type(clock=lambda: now[0])
                provider = provider_type(runtime)
                snapshots = []
                provider.changed.connect(lambda p=provider: snapshots.append(p.telemetry))
                runtime.feed(packet)
                self.assertTrue(provider.telemetry['connected'])
                self.assertTrue(provider.telemetry['freshness'][field])
                now[0] = runtime.STALE_SECONDS + 0.1
                loop = QEventLoop()
                QTimer.singleShot(400, loop.quit)
                loop.exec()
                self.assertFalse(snapshots[-1]['connected'])
                self.assertFalse(snapshots[-1]['freshness'][field])
                self.assertIsNone(snapshots[-1][field])
                self.assertFalse(runtime._expiry_timer.isActive())

    def test_expired_field_notifies_while_another_frame_keeps_connection_alive(self):
        examples = (
            (
                CrsfRuntime,
                CrsfProvider,
                frame(CRSF_FRAMETYPE_BATTERY_SENSOR, b'\x00\x98\x00\x0c\x00\x00\x01\x4b'),
                frame(0x14, b'\x01\x02\x03'),
                'batteryVoltage',
            ),
            (
                MspRuntime,
                MspProvider,
                response_v1(MSP_ALTITUDE, b'\x64\x00\x00\x00'),
                response_v1(1, b'\x00\x01\x02'),
                'altitude',
            ),
        )
        for runtime_type, provider_type, initial, later, field in examples:
            with self.subTest(provider=provider_type.__name__):
                now = [1.0]
                runtime = runtime_type(clock=lambda: now[0])
                provider = provider_type(runtime)
                snapshots = []
                provider.changed.connect(lambda p=provider: snapshots.append(p.telemetry))
                runtime.feed(initial)
                now[0] = 3.5
                runtime.feed(later)
                now[0] = 4.1
                loop = QEventLoop()
                QTimer.singleShot(400, loop.quit)
                loop.exec()
                self.assertTrue(snapshots[-1]['connected'])
                self.assertFalse(snapshots[-1]['freshness'][field])
                self.assertIsNone(snapshots[-1][field])
                runtime._expiry_timer.stop()


if __name__ == '__main__':
    unittest.main()
