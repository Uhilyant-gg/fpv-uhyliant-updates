"""Load OsdSettingsPanel.qml offscreen with a real Station."""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = r"""
import sys, tempfile
from pathlib import Path
from PySide6.QtCore import QObject, QSettings, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from backend import Station

app = QGuiApplication(sys.argv)
tmp = Path(tempfile.mkdtemp())
station = Station(QSettings(str(tmp / "s.ini"), QSettings.IniFormat))
engine = QQmlEngine()
engine.rootContext().setContextProperty("station", station)
component = QQmlComponent(engine, QUrl.fromLocalFile(str(Path("OsdSettingsPanel.qml").resolve())))
panel = component.create()
assert panel is not None, [e.toString() for e in component.errors()]
panel.setProperty("width", 1000); panel.setProperty("height", 680)
app.processEvents()
selector = panel.findChild(QObject, "osdLayoutSelector")
assert selector is not None
assert station.osdPosition == "corners"
assert selector.property("currentIndex") == 0
selector.activated.emit(2)
app.processEvents()
assert station.osdPosition == "top-right"
assert selector.property("currentIndex") == 2
assert panel.findChild(QObject, "osdPreviewOverlay").property("corner") == "top-right"
station.resetOSDStyle()
app.processEvents()
assert station.osdPosition == "corners"
assert selector.property("currentIndex") == 0
print("ok")
"""


def test_layout_selector_changes_station_layout():
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software")
    result = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        cwd=Path(__file__).resolve().parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
