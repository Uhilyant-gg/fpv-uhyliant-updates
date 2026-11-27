"""Load RecordingPanel.qml offscreen with a real DvrRuntime."""

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
from dvr_runtime import DvrRuntime

app = QGuiApplication(sys.argv)
tmp = Path(tempfile.mkdtemp())
opened = []
runtime = DvrRuntime(
    settings=QSettings(str(tmp / "s.ini"), QSettings.IniFormat),
    default_folder=str(tmp / "default"),
    open_url=lambda url: opened.append(url.toLocalFile()) or True,
)
engine = QQmlEngine()
engine.rootContext().setContextProperty("dvrRuntime", runtime)
component = QQmlComponent(engine, QUrl.fromLocalFile(str(Path("RecordingPanel.qml").resolve())))
panel = component.create()
assert panel is not None, [e.toString() for e in component.errors()]

def child(name):
    item = panel.findChild(QObject, name)
    assert item is not None, name
    return item

assert child("recordingFolderText").property("text") == str(tmp / "default") + "  (типова)"
assert not child("resetRecordingFolder").property("enabled")
assert child("recordingState").property("text") == "Записів у цьому сеансі ще немає."
assert runtime.setFolder(str(tmp / "my"))
app.processEvents()
assert child("recordingFolderText").property("text") == str(tmp / "my")
assert child("resetRecordingFolder").property("enabled")
assert child("recordingMessage").property("text") == "Нові записи зберігатимуться в цю папку."
child("openRecordingFolder").clicked.emit()
assert opened == [str(tmp / "my")]
child("resetRecordingFolder").clicked.emit()
app.processEvents()
assert child("recordingFolderText").property("text").endswith("(типова)")
print("ok")
"""


def test_folder_setting_through_panel():
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
