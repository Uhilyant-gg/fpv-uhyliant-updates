"""Load ControllerPanel.qml with a fake radio and drive the setup wizard through QML."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = r"""
import sys, tempfile
from pathlib import Path
from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from controller_onboarding import ControllerOnboarding
from controller_profile_store import JsonControllerProfileStore
from controller_runtime import ControllerRuntime

class Radio:
    frame = [1500, 1500, 1000, 1500]
    def poll(self):
        return [{"vendorId": 0x1209, "productId": 0x4F54, "name": "EdgeTX Radio", "channels": list(self.frame)}]

app = QGuiApplication(sys.argv)
radio = Radio()
store = JsonControllerProfileStore(Path(tempfile.mkdtemp()) / "c.json")
runtime = ControllerRuntime(ControllerOnboarding(radio, store), interval_ms=60000)
engine = QQmlEngine()
engine.rootContext().setContextProperty("controllerRuntime", runtime)
component = QQmlComponent(engine, QUrl.fromLocalFile(str(Path("ControllerPanel.qml").resolve())))
panel = component.create()
assert panel is not None, [e.toString() for e in component.errors()]

def text(name):
    item = panel.findChild(QObject, name)
    assert item is not None, name
    return item.property("text")

assert runtime.active, "panel must start polling when shown"
assert text("controllerName") == "EdgeTX Radio"
assert "Налаштуйте" in text("controllerSummary")
assert panel.findChild(QObject, "configureController").property("visible")

runtime.startWizard()
app.processEvents()
assert "центр" in text("wizardPrompt")
runtime.nextStep()
radio.frame = [1500, 1500, 1000, 1500]
runtime._tick(); runtime.nextStep()  # roll without movement -> human error
app.processEvents()
assert "Рух не помічено" in text("stepError"), text("stepError")

panel.deleteLater()
app.processEvents()
from PySide6.QtCore import QCoreApplication, QEvent
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)
assert not runtime.active, "closing the panel must stop polling"
assert not runtime.wizardActive, "closing the panel must cancel the wizard"
print("ok")
"""


class ControllerPanelQmlTests(unittest.TestCase):
    def test_panel_shows_status_and_drives_wizard(self):
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

    def test_preflight_shows_controller_row(self):
        script = r"""
import sys
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
app = QGuiApplication(sys.argv)
engine = QQmlEngine()
component = QQmlComponent(engine, QUrl.fromLocalFile(str(Path("PreflightPanel.qml").resolve())))
panel = component.create()
assert panel is not None, [e.toString() for e in component.errors()]
def row():
    checks = panel.property("checks")
    checks = checks.toVariant() if hasattr(checks, "toVariant") else checks
    return next(c for c in checks if c["label"] == "Пульт")
assert row()["state"] == "unavailable"
for health, state in (("ready", "ready"), ("attention", "attention"), ("problem", "error"), ("unknown", "unavailable")):
    panel.setProperty("controllerHealth", health)
    panel.setProperty("controllerDetail", "деталь")
    assert row()["state"] == state, (health, row())
    assert row()["detail"] == "деталь"
assert panel.stateLabel("attention") == "Потрібна дія"
print("ok")
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software")
        result = subprocess.run(
            [sys.executable, "-c", script],
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
