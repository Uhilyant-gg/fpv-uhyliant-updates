import unittest
from PySide6.QtCore import QObject, Signal
from serial_telemetry import CrsfSerialTransport, MspSerialTransport


class FakeRuntime(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.data = []

    def feed(self, data):
        self.data.append(data)


class SerialTransportTests(unittest.TestCase):
    def test_msp_transport_only_polls_allowlisted_read_commands(self):
        runtime = FakeRuntime()
        transport = MspSerialTransport(runtime)
        self.assertTrue(transport._poll_commands)
        self.assertEqual(transport.protocol, "MSP")
        transport.stop()

    def test_crsf_transport_is_passive_read_only(self):
        runtime = FakeRuntime()
        transport = CrsfSerialTransport(runtime)
        self.assertEqual(transport._poll_commands, ())
        self.assertEqual(transport.protocol, "CRSF")
        transport.stop()


if __name__ == "__main__":
    unittest.main()
