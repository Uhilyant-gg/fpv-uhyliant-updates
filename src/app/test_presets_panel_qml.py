"""Load PresetsPanel.qml offscreen with a real Station and preset store."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = r"""
import sys, tempfile
from pathlib import Path
from PySide6.QtCore import QObject, QSettings, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from backend import Station
from presets_runtime import PresetsRuntime
from settings_presets import PresetStore

app = QGuiApplication(sys.argv)
tmp = Path(tempfile.mkdtemp())
station = Station(QSettings(str(tmp / "s.ini"), QSettings.IniFormat))
runtime = PresetsRuntime(PresetStore(tmp / "presets.json"), station)
engine = QQmlEngine()
engine.rootContext().setContextProperty("presetsRuntime", runtime)
component = QQmlComponent(engine, QUrl.fromLocalFile(str(Path("PresetsPanel.qml").resolve())))
panel = component.create()
assert panel is not None, [e.toString() for e in component.errors()]

def child(name):
    item = panel.findChild(QObject, name)
    assert item is not None, name
    return item

assert child("activePresetText").property("text") == "Активного пресета немає"
child("newPresetName").setProperty("text", "Квадрик")
child("createPreset").clicked.emit()
app.processEvents()
assert child("newPresetName").property("text") == "", "name field clears after create"
assert "Квадрик" in child("activePresetText").property("text")
assert child("presetList").property("count") == 1
station.setAlertThreshold("cellCount", 6)
app.processEvents()
assert "незбережені" in child("activePresetText").property("text")
assert child("saveToActivePreset").property("enabled")
child("saveToActivePreset").clicked.emit()
app.processEvents()
assert "незбережені" not in child("activePresetText").property("text")
assert child("presetMessage").property("text") == "Налаштування збережено в пресет."
print("ok")
"""


class PresetsPanelQmlTests(unittest.TestCase):
    def test_create_and_save_through_panel(self):
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software")
        result = subprocess.run(
            [sys.executable, "-c", SCRIPT],
            cwd=Path(__file__).resolve().parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
