"""The default "corners" OSD layout spreads tiles and keeps bottom-right free for flight buttons."""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = r"""
import sys
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

app = QGuiApplication([])
engine = QQmlEngine()
component = QQmlComponent(engine, QUrl.fromLocalFile(sys.argv[1]))
overlay = component.create()
assert overlay is not None, [e.toString() for e in component.errors()]
assert overlay.property("corner") == "corners"
window = QQuickWindow()
overlay.setParentItem(window.contentItem())
overlay.setProperty("enabledElements", {"homeDistance": True, "video": True})
overlay.setProperty("telemetry", {"connected": True, "armed": False, "flightMode": "ACRO", "batteryVoltage": 16.1,
                                  "gpsFix": 3, "altitude": 12, "groundSpeed": 3, "heading": 90, "homeDistance": 40})
window.show()

def tiles():
    return {c.objectName()[4:]: c for c in overlay.childItems() if c.objectName().startswith("osd-") and c.isVisible()}

for width, height in ((1920, 1080), (1280, 720), (1024, 768)):
    window.resize(width, height)
    overlay.setWidth(width); overlay.setHeight(height)
    app.processEvents()
    overlay.refreshLayoutIssues()
    assert overlay.property("layoutIssues").toVariant() == [], (width, overlay.property("layoutIssues").toVariant())
    t = tiles()
    mx, my = overlay.property("safeMarginX"), overlay.property("safeMarginY")
    for name in ("link", "arm", "mode"):
        assert abs(t[name].x() - mx) < 1 and t[name].y() < height / 2, name
    for name in ("battery", "gps", "video"):
        assert abs(t[name].x() + t[name].width() - (width - mx)) < 1 and t[name].y() < height / 2, name
    for name in ("altitude", "speed", "heading", "homeDistance"):
        assert abs(t[name].x() - mx) < 1 and t[name].y() > height / 2, name
    assert t["link"].y() < t["arm"].y() < t["mode"].y()
    assert t["altitude"].y() < t["speed"].y() < t["heading"].y() < t["homeDistance"].y()
    assert abs(t["homeDistance"].y() + t["homeDistance"].height() - (height - my)) < 1
    for item in t.values():
        if item.objectName() in ("osd-reticle", "osd-horizon"):
            continue
        assert not (item.x() > width / 2 and item.y() > height / 2), "bottom-right stays free: " + item.objectName()

# A hidden tile leaves no gap in its corner.
overlay.setProperty("enabledElements", {"homeDistance": True, "video": True, "arm": False})
app.processEvents()
t = tiles()
assert "arm" not in t
step = t["link"].height() + 6
assert abs(t["mode"].y() - (t["link"].y() + step)) < 1

# A dragged tile keeps its own position.
overlay.setProperty("positions", {"battery": [50, 50]})
app.processEvents()
assert abs(tiles()["battery"].x() - overlay.width() / 2) < 1

# The classic one-corner stacks still work.
overlay.setProperty("positions", {})
overlay.setProperty("corner", "top-left")
app.processEvents()
t = tiles()
assert abs(t["battery"].x() - t["link"].x()) < 1
# Without a flight controller there are no empty "—" tiles; arranging the OSD shows them all.
overlay.setProperty("telemetry", {"connected": False})
overlay.setProperty("positions", {})
app.processEvents()
assert set(tiles()) <= {"video"}, set(tiles())
overlay.setProperty("editing", True)
app.processEvents()
assert {"link", "battery", "altitude"} <= set(tiles())
overlay.setProperty("editing", False)
overlay.setProperty("enabledElements", {})
overlay.setProperty("telemetry", {"connected": True, "batteryVoltage": 15.9})
app.processEvents()
assert set(tiles()) == {"link", "battery"}, set(tiles())
print("ok")
"""


def test_corners_layout():
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    path = str(Path(__file__).with_name("OsdOverlay.qml").resolve())
    result = subprocess.run([sys.executable, "-c", SCRIPT, path], capture_output=True, text=True, env=env, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
