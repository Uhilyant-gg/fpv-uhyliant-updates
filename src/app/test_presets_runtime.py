import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QSettings, QUrl

from backend import Station
from presets_runtime import PresetsRuntime
from settings_presets import PresetStore


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


class PresetsRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.station = Station(Settings())
        self.runtime = PresetsRuntime(PresetStore(self.dir / "presets.json"), self.station)

    def tearDown(self):
        self.tmp.cleanup()

    def test_configure_once_save_switch_and_restore(self):
        self.station.setAlertThreshold("cellCount", 4)
        self.assertTrue(self.runtime.createPreset("Квадрик 5\""))
        self.assertEqual(self.runtime.activeName, 'Квадрик 5"')
        self.assertFalse(self.runtime.dirty)

        self.station.setAlertThreshold("cellCount", 6)
        self.station.setOSDPosition("bottom-right")
        self.assertTrue(self.runtime.dirty)
        self.assertTrue(self.runtime.createPreset("Крило"))

        quad = next(p for p in self.runtime.presets if p["name"].startswith("Квадрик"))
        self.assertTrue(self.runtime.selectPreset(quad["id"]))
        self.assertEqual(self.station.alertThresholds["cellCount"], 4)
        self.assertEqual(self.station.osdPosition, "top-left")
        self.assertFalse(self.runtime.dirty)
        self.assertIn("Квадрик", self.runtime.message)

        self.station.setAlertThreshold("linkQualityMin", 70)
        self.assertTrue(self.runtime.dirty)
        self.assertTrue(self.runtime.saveToActive())
        self.assertFalse(self.runtime.dirty)

    def test_copy_rename_delete_with_human_errors(self):
        self.runtime.createPreset("A")
        first = self.runtime.presets[0]["id"]
        self.assertTrue(self.runtime.duplicatePreset(first))
        self.assertEqual([p["name"] for p in self.runtime.presets], ["A", "A (копія)"])
        copy_id = self.runtime.presets[1]["id"]
        self.assertFalse(self.runtime.renamePreset(copy_id, "a"))
        self.assertEqual(self.runtime.message, "Пресет з такою назвою вже є.")
        self.assertFalse(self.runtime.messageOk)
        self.assertTrue(self.runtime.renamePreset(copy_id, "B"))
        self.assertTrue(self.runtime.deletePreset(first))
        self.assertEqual(self.runtime.activeName, "")
        self.assertFalse(self.runtime.createPreset("   "))
        self.assertIn("назву", self.runtime.message)

    def test_export_and_import_through_file_urls(self):
        self.runtime.createPreset("Квадрик")
        preset_id = self.runtime.presets[0]["id"]
        target = QUrl.fromLocalFile(str(self.dir / "q.fpvpreset")).toString()
        self.assertTrue(self.runtime.exportPreset(preset_id, target))
        self.assertTrue(self.runtime.importPreset(target))
        self.assertEqual([p["name"] for p in self.runtime.presets], ["Квадрик", "Квадрик (2)"])
        bad = self.dir / "bad.fpvpreset"
        bad.write_text("nope", encoding="utf-8")
        self.assertFalse(self.runtime.importPreset(str(bad)))
        self.assertEqual(self.runtime.message, "Файл не є коректним пресетом FPV Uhyliant.")
        self.assertEqual(len(self.runtime.presets), 2)

    def test_corrupt_store_reports_without_crashing(self):
        (self.dir / "broken.json").write_text("{", encoding="utf-8")
        runtime = PresetsRuntime(PresetStore(self.dir / "broken.json"), self.station)
        self.assertEqual(runtime.presets, [])
        self.assertIn("пошкоджено", runtime.message)


if __name__ == "__main__":
    unittest.main()
