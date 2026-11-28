"""VideoPresetsPanel.qml with the real presets runtime: apply a slot, edit and save another."""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = r"""
import sys, tempfile
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
import video_presets as vp

app = QGuiApplication(sys.argv)

class Devices(QObject):
    changed = Signal()
    def __init__(self):
        super().__init__()
        self.activeId = 'c1'
    def get_name(self):
        return 'Квадрик'

class DevicesModel(QObject):
    changed = Signal()

class Connections:
    def control_host(self, device_id):
        return '10.147.17.5'

sent = []
runtime = vp.VideoPresetsRuntime(vp.VideoPresetStore(Path(tempfile.mkdtemp()) / 'v.json'), Devices(), Connections(),
                                 lambda host, lines: sent.append(lines) or {'state': 'applied'}, run_async=False)
from PySide6.QtCore import Property
from PySide6.QtQuick import QQuickView
class Model(QObject):
    changed = Signal()
    @Property(str, notify=changed)
    def activeName(self):
        return 'Квадрик'
model = Model()
view = QQuickView()
view.rootContext().setContextProperty('videoPresets', runtime)
view.rootContext().setContextProperty('devicesModel', model)
view.setResizeMode(QQuickView.SizeRootObjectToView)
view.setSource(QUrl.fromLocalFile(str(Path('VideoPresetsPanel.qml').resolve())))
assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
view.resize(860, 760)
view.show()
for _ in range(5):
    app.processEvents()
panel = view.rootObject()

def all_named(name):
    found = []
    def walk(item):
        if item.objectName() == name:
            found.append(item)
        for child in item.childItems() if isinstance(item, QQuickItem) else item.findChildren(QQuickItem):
            walk(child)
    walk(panel)
    return found

applies = all_named('videoPresetApply')
assert len(applies) == 9, len(applies)
assert all(a.property('enabled') for a in applies), 'every slot is filled by the station'
applies[2].clicked.emit()
app.processEvents()
assert runtime.activeKey == '4' and sent[0][3] == 'cli -s .video0.bitrate 2048'
message = all_named('videoPresetsMessage')[0]
assert message.property('text') == 'Пресет 4 «Слабкий канал» застосовано в камері'

auto = all_named('videoPresetsAuto')[0]
auto.toggle(); auto.toggled.emit()
app.processEvents()
assert runtime.auto and runtime.label.startswith('Авто · 4')
applies[1].clicked.emit()
app.processEvents()
assert not runtime.auto and runtime.activeKey == '3', 'a click by the pilot turns Auto off'
all_named('videoPresetEdit')[7].clicked.emit()
app.processEvents()
assert all_named('videoPresetEditor')[0].property('visible')
all_named('videoPresetName')[0].setProperty('text', 'Ніч')
all_named('videoPresetSave')[0].clicked.emit()
app.processEvents()
assert runtime.slots[7]['name'] == 'Ніч' and runtime.slots[7]['size'] == '1920x1080'
assert not all_named('videoPresetEditor')[0].property('visible')
print('ok')
"""


def test_video_presets_panel():
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
