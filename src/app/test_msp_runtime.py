import struct
import unittest
from msp_runtime import MSP_ALTITUDE, MSP_ATTITUDE, MSP_RAW_GPS, MspParser, MspRuntime, build_request, crc8_dvb_s2


def response_v1(command, payload=b''):
    checksum = len(payload) ^ command
    for value in payload:
        checksum ^= value
    return b'$M>' + bytes((len(payload), command)) + payload + bytes((checksum,))


class MspRuntimeTests(unittest.TestCase):
    def test_v1_parser_handles_fragmented_frame(self):
        parser = MspParser()
        frame = response_v1(MSP_ATTITUDE, struct.pack('<hhh', 125, -35, 270))
        self.assertEqual(parser.feed(frame[:4]), [])
        parsed = parser.feed(frame[4:])
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].command, MSP_ATTITUDE)

    def test_bad_checksum_is_rejected(self):
        parser = MspParser()
        frame = bytearray(response_v1(MSP_ALTITUDE, struct.pack('<i', 1234)))
        frame[-1] ^= 0xFF
        self.assertEqual(parser.feed(frame), [])
        self.assertEqual(parser.checksum_errors, 1)

    def test_read_only_allowlist_rejects_control_command(self):
        with self.assertRaises(ValueError):
            build_request(200)

    def test_runtime_decodes_received_values_only(self):
        now = [10.0]
        runtime = MspRuntime(clock=lambda: now[0])
        runtime.feed(response_v1(MSP_ATTITUDE, struct.pack('<hhh', 125, -35, 270)))
        runtime.feed(response_v1(MSP_RAW_GPS, struct.pack('<BBiihHH', 2, 11, 500000000, 300000000, 123, 450, 900)))
        telemetry = runtime.telemetry
        self.assertTrue(telemetry['connected'])
        self.assertEqual(telemetry['roll'], 12.5)
        self.assertEqual(telemetry['pitch'], -3.5)
        self.assertEqual(telemetry['groundSpeed'], 4.5)
        self.assertIsNone(telemetry['armed'])
        now[0] += runtime.STALE_SECONDS + 0.1
        stale = runtime.telemetry
        self.assertFalse(stale['connected'])
        self.assertEqual(stale['health'], 'stale')
        self.assertNotIn('roll', stale)

    def test_no_frame_observation_does_not_synthesize_disconnected(self):
        t = MspRuntime(clock=lambda: 10.0).telemetry
        self.assertIsNone(t['connected'])
        self.assertIsNone(t['health'])

    def test_v2_request_crc_is_self_consistent(self):
        request = build_request(MSP_ATTITUDE, version=2)
        self.assertEqual(request[:3], b'$X<')
        self.assertEqual(request[-1], crc8_dvb_s2(request[3:-1]))


if __name__ == '__main__':
    unittest.main()
