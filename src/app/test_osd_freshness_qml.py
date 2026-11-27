import os
from pathlib import Path
import subprocess
import sys
import unittest


class OsdFreshnessQmlTests(unittest.TestCase):
    def test_layout_diagnostics_remain_inside_safe_area_across_viewport_shapes(self):
        script = """
import sys
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
app = QGuiApplication([])
engine = QQmlEngine()
component = QQmlComponent(engine, QUrl.fromLocalFile(sys.argv[1]))
overlay = component.create()
if overlay is None:
    raise RuntimeError([error.toString() for error in component.errors()])
window = QQuickWindow()
overlay.setParentItem(window.contentItem())
overlay.setProperty('editing', True)
overlay.setProperty('enabledElements', {'homeDistance': True})
window.show()
for width, height in ((1280, 720), (1024, 768), (600, 600), (480, 854)):
    window.resize(width, height)
    overlay.setWidth(width); overlay.setHeight(height)
    app.processEvents()
    overlay.refreshLayoutIssues()
    assert overlay.property('layoutIssues').toVariant() == [], (width, height, overlay.property('layoutIssues').toVariant())
    for name in ('osd-link', 'osd-battery', 'osd-homeDistance'):
        item = next((child for child in overlay.childItems() if child.objectName() == name), None)
        assert item is not None, name
        assert item.x() >= overlay.property('safeMarginX'), (width, height, name, item.x())
        assert item.y() >= overlay.property('safeMarginY'), (width, height, name, item.y())
overlay.setProperty('positions', {'link': [25, 25], 'battery': [25, 25]})
app.processEvents()
overlay.refreshLayoutIssues()
issues = overlay.property('layoutIssues').toVariant()
assert any(issue.get('kind') == 'overlap' and {issue.get('first'), issue.get('second')} == {'link', 'battery'} for issue in issues), issues
overlay.setProperty('positions', {'link': [0, 0]})
app.processEvents()
overlay.refreshLayoutIssues()
issues = overlay.property('layoutIssues').toVariant()
assert any(issue.get('kind') == 'safe-area' and issue.get('name') == 'link' for issue in issues), issues
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        path = str(Path(__file__).with_name("OsdOverlay.qml").resolve())
        result = subprocess.run(
            [sys.executable, "-c", script, path], capture_output=True, text=True, env=env, timeout=30
        )
        self.assertEqual(result.returncode, 0, result.stderr)

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
QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(round(tile.x() + 8), round(tile.y() + 8)))
QTest.mouseMove(window, QPoint(310, 260), 50)
app.processEvents()
assert abs(tile.x() / (overlay.width() / 20) - round(tile.x() / (overlay.width() / 20))) < 0.01, tile.x()
QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(310, 260))
app.processEvents()
assert saved and saved[0][0] == 'link', saved
name, x, y = saved[0]
assert 0 < x < 100 and 0 < y < 100 and x % 5 == 0 and y % 5 == 0, saved
QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(round(tile.x() + 8), round(tile.y() + 8)))
QTest.mouseMove(window, QPoint(790, 590), 50)
QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(790, 590))
app.processEvents()
assert tile.x() + tile.width() <= overlay.width() + 0.01, (tile.x(), tile.width(), overlay.width())
assert saved[-1][1] % 5 == 0 and saved[-1][2] % 5 == 0, saved
old_x = tile.x()
overlay.setWidth(1000); app.processEvents()
assert tile.x() > old_x, (tile.x(), old_x)
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        path = str(Path(__file__).with_name("OsdOverlay.qml").resolve())
        result = subprocess.run(
            [sys.executable, "-c", script, path], capture_output=True, text=True, env=env, timeout=30
        )
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
overlay.setProperty('telemetry', {'connected': True, 'linkQuality': 98, 'rssiDbm': -72, 'freshness': {'linkQuality': True, 'rssiDbm': True}})
assert overlay.linkDetails() == ' · LQ 98% · -72 dBm', overlay.linkDetails()
overlay.setProperty('telemetry', {'connected': True, 'freshness': {'linkQuality': False}})
assert overlay.linkDetails() == ' · LQ застаріло', overlay.linkDetails()
overlay.setProperty('telemetry', {'connected': True})
assert overlay.linkDetails() == '', overlay.linkDetails()
overlay.setProperty('telemetry', {'connected': True, 'heading': 90, 'homeBearing': 0})
assert overlay.homeArrow() == ' ←', overlay.homeArrow()
overlay.setProperty('telemetry', {'connected': True, 'heading': 350, 'homeBearing': 40})
assert overlay.homeArrow() == ' ↗', overlay.homeArrow()
overlay.setProperty('telemetry', {'connected': True, 'heading': 0, 'homeBearing': 180, 'freshness': {'homeBearing': False}})
assert overlay.homeArrow() == '', overlay.homeArrow()
overlay.setProperty('telemetry', {'connected': True, 'heading': 0, 'homeBearing': None})
assert overlay.homeArrow() == '', overlay.homeArrow()
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        path = str(Path(__file__).with_name("OsdOverlay.qml").resolve())
        result = subprocess.run(
            [sys.executable, "-c", script, path], capture_output=True, text=True, env=env, timeout=30
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_optional_osd_widgets_follow_individual_visibility_and_attitude_freshness(self):
        script = """
import sys
from PySide6.QtCore import QObject, QPoint, QUrl, Qt
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
reticle = overlay.findChild(QObject, 'osd-reticle')
horizon = overlay.findChild(QObject, 'osd-horizon')
assert reticle is not None and horizon is not None
overlay.setProperty('enabledElements', {'reticle': True, 'horizon': True, 'battery': False, 'homeDistance': True})
overlay.setProperty('telemetry', {'connected': True, 'roll': 12, 'pitch': -4, 'homeDistance': 80})
saved = []
overlay.positionChanged.connect(lambda name, x, y: saved.append((name, x, y)))
window.show()
app.processEvents()
assert reticle.property('visible') and horizon.property('visible')
assert overlay.findChild(QObject, 'osd-battery') is None
QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(400, 300))
QTest.mouseMove(window, QPoint(520, 390), 50)
app.processEvents()
center_x = reticle.x() + reticle.width() / 2
assert abs(center_x / (overlay.width() / 20) - round(center_x / (overlay.width() / 20))) < 0.01
QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(520, 390))
app.processEvents()
assert saved and saved[0][0] == 'reticle' and saved[0][1] % 5 == 0 and saved[0][2] % 5 == 0, saved
overlay.setProperty('telemetry', {'connected': True, 'freshness': {'roll': False}, 'roll': 12, 'pitch': -4})
app.processEvents()
unavailable = horizon.findChild(QObject, 'osd-horizon-unavailable')
assert unavailable is not None and unavailable.property('visible')
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        path = str(Path(__file__).with_name("OsdOverlay.qml").resolve())
        result = subprocess.run(
            [sys.executable, "-c", script, path], capture_output=True, text=True, env=env, timeout=30
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
