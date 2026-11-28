"""The map draws the drone from its flight controller's GPS, its trail and home, and follows it."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = r"""
import sys, time
from PySide6.QtCore import Property, QObject, QUrl, Signal, QStandardPaths
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

QStandardPaths.setTestModeEnabled(True)
app = QGuiApplication([])

class Telemetry(QObject):
    changed = Signal()
    def __init__(self):
        super().__init__()
        self._t = {"connected": False}
    @Property("QVariantMap", notify=changed)
    def telemetry(self):
        return self._t
    def set(self, **t):
        self._t = t
        self.changed.emit()

tel = Telemetry()
engine = QQmlEngine()
engine.rootContext().setContextProperty("telemetryRuntime", tel)
component = QQmlComponent(engine, QUrl.fromLocalFile(sys.argv[1]))
item = component.create()
assert item is not None, [e.toString() for e in component.errors()]
window = QQuickWindow()
item.setParentItem(window.contentItem())
item.setWidth(640); item.setHeight(360)
window.resize(640, 360)
window.show()

def child(name):
    def walk(i):
        if i.objectName() == name:
            return i
        for c in i.childItems():
            f = walk(c)
            if f is not None:
                return f
    return walk(item)

def pump(seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.02)

pump(0.3)
assert not item.property("hasDrone")
assert child("flightMapNoDrone").isVisible(), "the pilot is told the map waits for coordinates"

tel.set(connected=True, latitude=50.45, longitude=30.52, heading=90, homeLatitude=50.44, homeLongitude=30.52)
pump(0.3)
assert item.property("hasDrone") and item.property("hasHome")
assert not child("flightMapNoDrone").isVisible()
assert abs(item.property("centerLatitude") - 50.45) < 1e-6 and abs(item.property("centerLongitude") - 30.52) < 1e-6, "the map follows the drone"
assert child("flightMapView") is not None
tel.set(connected=True, latitude=50.46, longitude=30.52, heading=90, homeLatitude=50.44, homeLongitude=30.52)
pump(1.3)
assert item.property("trailLength") == 2, item.property("trailLength")

course = item.findChild(QObject, "flightMapCourseUp")
course.clicked.emit()
pump(0.2)
assert abs(item.property("mapBearing") - 90) < 0.5, "course up: the map turns with the drone"
course.clicked.emit()
pump(0.2)

# The wheel zooms one step a notch; while following, around the drone.
from PySide6.QtCore import QPointF
zoom = item.property("zoom")
item.zoomAt(-2, QPointF(100, 100))
pump(0.2)
assert abs(item.property("zoom") - (zoom - 2)) < 0.01, (zoom, item.property("zoom"))
assert abs(item.property("centerLatitude") - 50.46) < 1e-6, "following: the drone stays in the middle"
assert item.findChild(QObject, "flightMapFollow").property("on"), "a zoom is not a pan"
pump(0.4)

# A pan by the pilot turns following off.
item.panTo(50.0, 30.0)
pump(0.6)
assert not item.findChild(QObject, "flightMapFollow").property("on")
print("ok")
"""


def test_flight_map_shows_and_follows_the_drone():
    with tempfile.TemporaryDirectory() as home:
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software", HOME=home, XDG_DATA_HOME=home)
        result = subprocess.run(
            [sys.executable, "-c", SCRIPT, str(Path(__file__).resolve().parent / "FlightMap.qml")],
            cwd=Path(__file__).resolve().parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
