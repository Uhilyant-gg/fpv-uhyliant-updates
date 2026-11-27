import json
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QSettings

import station_backup
from backend import Station
from settings_presets import PresetStore
from station_backup import StationBackup
from station_settings import default_settings
from test_station_backup import Devices


class Settings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass

    def status(self):
        return QSettings.NoError


class BackupWithPresetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def station(self):
        return Station(Settings())

    def test_backup_restores_presets_and_settings_on_another_station(self):
        source_station = self.station()
        source_station.setAlertThreshold("cellCount", 6)
        source_presets = PresetStore(self.dir / "a.json")
        quad = default_settings()
        quad["alerts"]["cellCount"] = 4
        source_presets.create("Квадрик", quad)
        source_presets.create("Крило", default_settings(), activate=False)
        path = self.dir / "backup.fub"
        self.assertTrue(
            StationBackup(Devices(), station=source_station, presets=source_presets).exportEncrypted(
                str(path), "correct horse"
            )
        )

        target_station = self.station()
        target_presets = PresetStore(self.dir / "b.json")
        target_presets.create("Старий", default_settings())
        devices = Devices()
        backup = StationBackup(devices, station=target_station, presets=target_presets)
        restored_signals = []
        backup.restored.connect(lambda: restored_signals.append(True))
        plan = backup.inspectEncryptedImport(str(path), "correct horse")
        self.assertEqual(plan["presetCount"], 2)
        self.assertTrue(plan["includesSettings"])
        self.assertEqual(target_presets.load()["presets"][0]["name"], "Старий", "inspect must not change data")

        self.assertTrue(backup.restoreInspected(True))
        self.assertEqual([p["name"] for p in target_presets.load()["presets"]], ["Квадрик", "Крило"])
        self.assertEqual(target_station.alertThresholds["cellCount"], 6)
        self.assertIsNotNone(devices.restored)
        self.assertEqual(restored_signals, [True])
        self.assertIn("пресети", backup.result["reason"])

    def test_version_3_backups_still_restore_devices_only(self):
        path = self.dir / "old.fub"
        original_version = station_backup.VERSION
        station_backup.VERSION = 3
        try:
            self.assertTrue(StationBackup(Devices()).exportEncrypted(str(path), "correct horse"))
        finally:
            station_backup.VERSION = original_version
        self.assertEqual(json.loads(path.read_text())["version"], 3)
        presets = PresetStore(self.dir / "p.json")
        presets.create("Мій", default_settings())
        devices = Devices()
        backup = StationBackup(devices, station=self.station(), presets=presets)
        plan = backup.inspectEncryptedImport(str(path), "correct horse")
        self.assertEqual(plan["version"], 3)
        self.assertEqual(plan["presetCount"], 0)
        self.assertTrue(backup.restoreInspected(True))
        self.assertIsNotNone(devices.restored)
        self.assertEqual([p["name"] for p in presets.load()["presets"]], ["Мій"], "old backups keep current presets")

    def test_invalid_presets_in_backup_reject_the_whole_restore(self):
        presets = PresetStore(self.dir / "p.json")
        backup = StationBackup(Devices(), station=self.station(), presets=presets)
        original = backup._payload

        def tampered():
            payload = original()
            payload["presets"] = {"active": None, "presets": [{"id": "x", "name": "", "settings": {}}]}
            return payload

        backup._payload = tampered
        path = self.dir / "bad.fub"
        self.assertTrue(backup.exportEncrypted(str(path), "correct horse"))
        devices = Devices()
        target = StationBackup(devices, station=self.station(), presets=presets)
        self.assertEqual(target.inspectEncryptedImport(str(path), "correct horse"), {})
        self.assertIsNone(devices.restored)


if __name__ == "__main__":
    unittest.main()
