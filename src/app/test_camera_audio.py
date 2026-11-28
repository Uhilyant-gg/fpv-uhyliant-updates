import io
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QObject, Signal

import camera_audio as ca

APP = QCoreApplication.instance() or QCoreApplication([])


class Features(QObject):
    changed = Signal()

    def __init__(self, supported=True, enabled=True):
        super().__init__()
        self.audioSupported = supported
        self.micEnabled = enabled
        self.micRate = 8000
        self.audioText = "у прошивці FPV звуку немає (потрібна Lite або Ultimate)"


class Devices:
    activeId = "cam"


class Connections:
    host = "192.168.1.10"

    def control_host(self, device_id):
        return self.host


class Sink:
    def __init__(self):
        self.data = b""
        self.volume = None
        self.stopped = False

    def write(self, pcm):
        self.data += pcm

    def setVolume(self, volume):
        self.volume = volume

    def stop(self):
        self.stopped = True


class Response:
    def __init__(self, data):
        self.stream = io.BytesIO(data)

    def read(self, n):
        return self.stream.read(n)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.features = Features()
        self.sinks = []
        self.requests = []
        self.replies = {"/audio.alaw": [(401, None), (200, Response(bytes([0xD5]) * 300))]}

        def opener(host, path, login):
            self.requests.append((host, path, login))
            queue = self.replies.get(path, [(404, None)])
            return queue.pop(0) if len(queue) > 1 else queue[0]

        def sink_factory(rate):
            sink = Sink()
            self.sinks.append(sink)
            return sink

        self.runtime = ca.AudioRuntime(
            Devices(),
            Connections(),
            self.features,
            logins=lambda: [("root", "12345")],
            store_path=Path(self.temp.name) / "audio.json",
            opener=opener,
            sink_factory=sink_factory,
            run_async=False,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_alaw_decoding(self):
        self.assertEqual(ca.alaw_to_pcm(bytes([0xD5])), (8).to_bytes(2, "little", signed=True))
        self.assertEqual(ca.alaw_to_pcm(bytes([0x55])), (-8).to_bytes(2, "little", signed=True))
        self.assertEqual(len(ca.alaw_to_pcm(bytes(range(256)))), 512)
        loudest = int.from_bytes(ca.alaw_to_pcm(bytes([0xAA])), "little", signed=True)
        self.assertEqual(loudest, 32256)

    def test_plays_in_flight_with_the_camera_login(self):
        self.runtime.setActive(True)
        self.assertEqual([r[2] for r in self.requests], [None, ("root", "12345")])
        self.assertEqual(len(self.sinks[0].data), 600)
        self.assertEqual(self.sinks[0].volume, 0.8)

    def test_falls_back_to_pcm(self):
        self.replies = {"/audio.pcm": [(200, Response(b"\x01\x02" * 10))]}
        self.runtime.setActive(True)
        self.assertEqual(self.sinks[0].data, b"\x01\x02" * 10)

    def test_muted_sound_is_not_fetched_and_remembered(self):
        self.runtime.setMuted(True)
        self.runtime.setActive(True)
        self.assertEqual(self.requests, [])
        self.assertIn("вимкнено на станції", self.runtime.text)
        self.runtime.setVolume(35)
        again = ca.AudioRuntime(Devices(), Connections(), self.features, store_path=Path(self.temp.name) / "audio.json")
        self.assertTrue(again.muted)
        self.assertEqual(again.volume, 35)

    def test_fpv_firmware_explains_why_there_is_no_sound(self):
        self.features.audioSupported = False
        self.features.micEnabled = False
        self.runtime.setActive(True)
        self.assertEqual(self.requests, [])
        self.assertIn("FPV", self.runtime.text)

    def test_microphone_switched_on_later_starts_the_sound(self):
        self.features.micEnabled = False
        self.runtime.setActive(True)
        self.assertEqual(self.requests, [])
        self.features.micEnabled = True
        self.features.changed.emit()
        self.assertTrue(self.requests)

    def test_no_sound_output_on_the_pc(self):
        self.runtime._sink_factory = lambda rate: None
        self.runtime.setActive(True)
        self.assertIn("немає виходу звуку", self.runtime.text)

    def test_only_private_addresses(self):
        with self.assertRaises(PermissionError):
            ca.open_stream("8.8.8.8", "/audio.alaw")
        self.assertEqual(ca.http_host("fd00::1"), "[fd00::1]")


if __name__ == "__main__":
    unittest.main()
