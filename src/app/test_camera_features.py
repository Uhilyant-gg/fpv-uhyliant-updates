import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication

import camera_features as cf
import devices as devices_module

APP = QCoreApplication.instance() or QCoreApplication([])

FPV_RELEASE = 'NAME="OpenIPC"\nBUILD_OPTION="fpv"\n'
LITE_RELEASE = 'NAME="OpenIPC"\nBUILD_OPTION="lite"\n'


def answers(**over):
    base = {
        "release": (0, LITE_RELEASE),
        "video1": (0, "false"),
        "usbEnabled": (1, ""),
        "usbCodec": (1, ""),
        "usbDevices": (1, ""),
        "audioEnabled": (0, "false"),
        "audioRate": (0, "8000"),
        "audioVolume": (0, "30"),
    }
    base.update(over)
    return base


class ParseTests(unittest.TestCase):
    def test_second_stream_appears_when_on(self):
        self.assertEqual(cf.streams_for(cf.parse_features(answers())), [])
        streams = cf.streams_for(cf.parse_features(answers(video1=(0, "true"))))
        self.assertEqual([(s["path"], s["kind"]) for s in streams], [("/stream=1", "sub")])

    def test_usb_device_on_a_firmware_that_encodes_it(self):
        features = cf.parse_features(answers(usbEnabled=(0, "false"), usbDevices=(0, "USB Camera: P2 Pro\n")))
        self.assertTrue(cf.usb_needs_enabling(features))
        self.assertEqual(cf.streams_for(features), [])
        self.assertIn("увімкну", cf.usb_text(features))
        features["usb"]["enabled"] = True
        stream = cf.streams_for(features)[0]
        self.assertEqual((stream["name"], stream["kind"], stream["path"]), ("Тепловізор", "thermal", "/stream=3"))

    def test_usb_capture_card_is_named_usb_camera(self):
        features = cf.parse_features(answers(usbEnabled=(0, "true"), usbDevices=(0, "UVC Capture HDMI")))
        self.assertEqual(cf.streams_for(features)[0]["name"], "USB-камера")
        self.assertFalse(cf.usb_needs_enabling(features))

    def test_usb_device_on_a_firmware_without_usbcam(self):
        features = cf.parse_features(answers(usbDevices=(0, "UVC Camera")))
        self.assertFalse(features["usb"]["supported"])
        self.assertFalse(cf.usb_needs_enabling(features))
        self.assertIn("не вміє кодувати", cf.usb_text(features))

    def test_fpv_firmware_has_no_sound(self):
        features = cf.parse_features(answers(release=(0, FPV_RELEASE), audioEnabled=(0, "true")))
        self.assertFalse(features["audio"]["supported"])
        self.assertIn("FPV", cf.audio_text(features))

    def test_lite_firmware_microphone(self):
        features = cf.parse_features(answers(audioEnabled=(0, "true"), audioRate=(0, "16000")))
        self.assertTrue(features["audio"]["enabled"])
        self.assertEqual(features["audio"]["rate"], 16000)
        self.assertEqual(features["audio"]["volume"], 30)
        self.assertIn("16 кГц", cf.audio_text(features))

    def test_audio_commands_take_only_checked_values(self):
        self.assertEqual(
            cf.audio_commands(enabled=True, volume=250),
            ["cli -s .audio.enabled true", "cli -s .audio.volume 100", cf.RELOAD],
        )
        self.assertEqual(cf.audio_commands(rate=16000), ["cli -s .audio.srate 16000", cf.RELOAD])
        with self.assertRaises(ValueError):
            cf.audio_commands(rate=12345)
        self.assertEqual(cf.audio_commands(), [])


class FakeSession:
    def __init__(self, replies):
        self.replies = replies
        self.sent = []

    def run(self, command):
        self.sent.append(command)
        for key, line in cf.READ_COMMANDS.items():
            if line == command:
                return self.replies.get(key, (1, ""))
        return (0, "")


class FakeShell:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *exc):
        return False


class FakeConnections:
    def control_host(self, device_id):
        return "192.168.1.10"


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        devices_module.DATA = root
        devices_module.DB = root / "devices.sqlite3"
        devices_module.LEGACY_DB = root / "devices.json"
        self.orig = devices_module.interfaces
        devices_module.interfaces = lambda: []
        self.devices = devices_module.Devices()
        self.did = self.devices.addDevice("Cam", "OpenIPC", "192.168.1.10", 80, "Network", "")
        with self.devices._connect() as db:
            db.execute("UPDATE devices SET active=1 WHERE id=?", (self.did,))
        self.devices._load()
        self.session = FakeSession(answers(video1=(0, "true")))
        self.armed = False
        self.runtime = cf.CameraFeaturesRuntime(
            self.devices,
            FakeConnections(),
            lambda host: FakeShell(self.session),
            may_restart_video=lambda: not self.armed,
            run_async=False,
        )

    def tearDown(self):
        devices_module.interfaces = self.orig
        self.temp.cleanup()

    def paths(self):
        return sorted(s["path"] for s in self.devices.activeStreams)

    def test_streams_come_and_go_by_themselves(self):
        self.runtime.poll()
        self.assertEqual(self.paths(), ["/stream=1"])
        self.session.replies["video1"] = (0, "false")
        self.runtime.poll()
        self.assertEqual(self.paths(), [])
        self.session.replies["video1"] = (0, "true")
        self.runtime.poll()
        self.assertEqual(self.paths(), ["/stream=1"])
        self.assertEqual(len([s for s in self.devices.streams if s["path"] == "/stream=1"]), 1)

    def test_usb_is_switched_on_only_when_not_armed(self):
        self.session.replies.update(usbEnabled=(0, "false"), usbDevices=(0, "UVC Camera"))
        self.armed = True
        self.runtime.poll()
        self.assertNotIn("cli -s .usbcam.enabled true", self.session.sent)
        self.armed = False
        self.runtime._usb_tried_at = -1e9
        self.runtime.poll()
        self.assertIn("cli -s .usbcam.enabled true", self.session.sent)
        self.assertIn("cli -s .usbcam.codec transcode", self.session.sent)

    def test_failed_read_changes_nothing(self):
        self.runtime.poll()
        self.session.run = lambda command: (_ for _ in ()).throw(OSError("gone"))
        self.runtime.poll()
        self.assertEqual(self.paths(), ["/stream=1"])

    def test_microphone_switch(self):
        self.runtime.poll()
        self.runtime.setMicEnabled(True)
        self.assertIn("cli -s .audio.enabled true", self.session.sent)


if __name__ == "__main__":
    unittest.main()
