import os
from pathlib import Path
import subprocess
import sys
import unittest


class OsdFreshnessQmlTests(unittest.TestCase):
    def test_dragging_snaps_and_restores_position_after_resize(self):
        script = """
import sys
from PySide6.QtCore import QUrl, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
app = QGuiApplication([])
engine = QQmlEngine()
component = QQmlComponent(engine, QUrl.fromLocalFile(sys.argv[1]))
overlay = component.create()
if overlay is None:
    raise RuntimeError([error.toString() for error in component.errors()])
window = QQuickWindow()
window.resize(800, 600)
overlay.setParentItem(window.contentItem())
overlay.setWidth(800); overlay.setHeight(600); overlay.setProperty('editing', True)
saved = []
def persist(name, x, y):
    saved.append((name, x, y))
    overlay.setProperty('positions', {name: [x, y]})
overlay.positionChanged.connect(persist)
window.show(); app.processEvents()
tile = next((child for child in overlay.childItems() if child.objectName() == 'osd-link'), None)
assert tile is not None
QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(10, 10))
QTest.mouseMove(window, QPoint(310, 260), 50)
QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(310, 260))
app.processEvents()
assert saved and saved[0][0] == 'link', saved
name, x, y = saved[0]
assert 0 < x < 100 and 0 < y < 100 and x % 5 == 0 and y % 5 == 0, saved
old_x = tile.x()
overlay.setWidth(1000); app.processEvents()
assert tile.x() > old_x, (tile.x(), old_x)
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        path = str(Path(__file__).with_name("OsdOverlay.qml").resolve())
        result = subprocess.run([sys.executable, "-c", script, path], capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_qml_hides_expired_values_and_distinguishes_unknown(self):
        script = """
import sys
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
app = QGuiApplication([])
engine = QQmlEngine()
component = QQmlComponent(engine, QUrl.fromLocalFile(sys.argv[1]))
overlay = component.create()
if overlay is None:
    raise RuntimeError([error.toString() for error in component.errors()])
overlay.setProperty('telemetry', {'connected': True, 'freshness': {'altitude': False, 'gpsFix': False}, 'gpsFix': 3})
assert overlay.telemetryText('altitude', 123, ' м', 0) == 'застаріло'
assert overlay.gpsFixDisplay() == 'застаріло'
assert overlay.telemetryText('heading', None, '°', 0) == '—'
overlay.setProperty('telemetry', {'connected': True, 'freshness': {'altitude': True}})
assert overlay.telemetryText('altitude', 123, ' м', 0) == '123 м'
overlay.setProperty('telemetry', {'connected': False})
assert overlay.telemetryText('altitude', 123, ' м', 0) == '—'
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        path = str(Path(__file__).with_name("OsdOverlay.qml").resolve())
        result = subprocess.run([sys.executable, "-c", script, path], capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
