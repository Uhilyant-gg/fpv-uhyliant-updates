import unittest
from crsf_runtime import CRSF_FRAMETYPE_BATTERY_SENSOR, CRSF_FRAMETYPE_GPS, CrsfParser, CrsfRuntime, crc8_dvb_s2


def frame(frame_type, payload, address=0xC8):
    body = bytes((frame_type,)) + payload
    return bytes((address, len(body) + 1)) + body + bytes((crc8_dvb_s2(body),))


class CrsfRuntimeTests(unittest.TestCase):
    def test_fragmented_frame(self):
        parser = CrsfParser()
        raw = frame(CRSF_FRAMETYPE_BATTERY_SENSOR, b'\x00\x98\x00\x0c\x00\x00\x01\x4b')
        self.assertEqual(parser.feed(raw[:3]), [])
        parsed = parser.feed(raw[3:])
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].frame_type, CRSF_FRAMETYPE_BATTERY_SENSOR)

    def test_bad_crc_is_rejected(self):
        parser = CrsfParser()
        raw = bytearray(frame(CRSF_FRAMETYPE_BATTERY_SENSOR, b'\x00\x98\x00\x0c\x00\x00\x01\x4b'))
        raw[-1] ^= 0xFF
        self.assertEqual(parser.feed(raw), [])
        self.assertEqual(parser.crc_errors, 1)

    def test_received_battery_and_gps_are_normalized_with_field_freshness(self):
        now = [20.0]
        runtime = CrsfRuntime(clock=lambda: now[0])
        runtime.feed(frame(CRSF_FRAMETYPE_BATTERY_SENSOR, b'\x00\x98\x00\x0c\x00\x00\x01\x4b'))
        gps = (500000000).to_bytes(4, 'big', signed=True) + (300000000).to_bytes(4, 'big', signed=True)
        gps += (450).to_bytes(2, 'big') + (9000).to_bytes(2, 'big') + (1123).to_bytes(2, 'big') + bytes((11,))
        runtime.feed(frame(CRSF_FRAMETYPE_GPS, gps))
        telemetry = runtime.telemetry
        self.assertTrue(telemetry['connected'])
        self.assertTrue(telemetry['freshness']['batteryVoltage'])
        self.assertEqual(telemetry['batteryVoltage'], 15.2)
        self.assertEqual(telemetry['current'], 1.2)
        self.assertEqual(telemetry['batteryRemaining'], 75)
        self.assertEqual(telemetry['groundSpeed'], 45.0)
        self.assertEqual(telemetry['heading'], 90.0)
        self.assertEqual(telemetry['altitude'], 123.0)
        self.assertEqual(telemetry['satellites'], 11)
        self.assertIsNone(telemetry['armed'])
        now[0] += runtime.STALE_SECONDS + 0.1
        stale = runtime.telemetry
        self.assertFalse(stale['connected'])
        self.assertEqual(stale['health'], 'stale')
        self.assertNotIn('batteryVoltage', stale)
        self.assertFalse(stale['freshness']['batteryVoltage'])

    def test_no_frame_observation_does_not_synthesize_disconnected(self):
        t = CrsfRuntime(clock=lambda: 20.0).telemetry
        self.assertIsNone(t['connected'])
        self.assertIsNone(t['health'])

    def test_field_freshness_is_independent_of_recent_link_frames(self):
        now = [20.0]
        runtime = CrsfRuntime(clock=lambda: now[0])
        runtime.feed(frame(CRSF_FRAMETYPE_BATTERY_SENSOR, b'\x00\x98\x00\x0c\x00\x00\x01\x4b'))
        now[0] += 2.5
        gps = (
            (500000000).to_bytes(4, 'big', signed=True)
            + (300000000).to_bytes(4, 'big', signed=True)
            + (450).to_bytes(2, 'big')
            + (9000).to_bytes(2, 'big')
            + (1123).to_bytes(2, 'big')
            + bytes((11,))
        )
        runtime.feed(frame(CRSF_FRAMETYPE_GPS, gps))
        now[0] += 1.0
        telemetry = runtime.telemetry
        self.assertTrue(telemetry['connected'])
        self.assertFalse(telemetry['freshness']['batteryVoltage'])
        self.assertNotIn('batteryVoltage', telemetry)
        self.assertTrue(telemetry['freshness']['groundSpeed'])
        self.assertEqual(telemetry['groundSpeed'], 45.0)


if __name__ == '__main__':
    unittest.main()
