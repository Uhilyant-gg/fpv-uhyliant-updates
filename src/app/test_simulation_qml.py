import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SimulationQmlTests(unittest.TestCase):
    def test_simulation_uses_flight_workspace_without_touching_real_telemetry(self):
        script = """
import sys
from pathlib import Path
from PySide6.QtCore import QObject, QSettings, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem
import backend, updater_engine
test_root = Path(sys.argv[1])
original_station = backend.Station
backend.Station = lambda: original_station(QSettings(str(test_root / 'settings.ini'), QSettings.IniFormat))
updater_engine.Updater.check = lambda self: None
original_single_shot = QTimer.singleShot
def single_shot(delay, callback):
    if getattr(callback, '__name__', '') != 'show_home':
        return original_single_shot(delay, callback)
    def verify():
        callback()
        app = QGuiApplication.instance()
        window = next(w for w in app.topLevelWindows() if w.property('simulation') is not None)
        def value_map(value):
            return value.toVariant() if hasattr(value, 'toVariant') else value
        before = value_map(window.property('t'))
        menu_toggle = window.findChild(QObject, 'mainMenuToggle')
        assert menu_toggle is not None
        menu_toggle.clicked.emit()
        app.processEvents()
        drawer = window.findChild(QObject, 'mainMenuDrawer')
        assert drawer is not None
        def find_item(item, name):
            if item.objectName() == name:
                return item
            for child in item.childItems():
                found = find_item(child, name)
                if found is not None:
                    return found
            return None
        button = find_item(drawer, 'menu-simulation')
        assert button is not None, [(child.objectName(), child.metaObject().className()) for child in drawer.childItems()]
        button.clicked.emit()
        app.processEvents()
        assert window.property('simulation') is True
        assert window.findChild(QObject, 'mainPages').property('currentIndex') == 1
        scene = window.findChild(QObject, 'simulationWorld')
        video = window.findChild(QObject, 'mainFlightVideoOutput')
        assert scene is not None and scene.property('visible')
        assert video is not None and not video.property('visible')
        first = value_map(window.property('simulatedTelemetry'))
        assert all(field in first for field in ('roll', 'pitch', 'yaw', 'homeDistance', 'batteryVoltage', 'gpsFix', 'groundSpeed'))
        window.setProperty('simulationTick', 10)
        app.processEvents()
        second = value_map(window.property('simulatedTelemetry'))
        assert first['heading'] != second['heading'] and first['roll'] != second['roll']
        assert value_map(window.property('t')) == before
        menu_toggle = window.findChild(QObject, 'flightMenuToggle')
        assert menu_toggle is not None
        menu_toggle.clicked.emit()
        app.processEvents()
        menu = window.findChild(QObject, 'flightMenu')
        assert menu is not None and menu.property('visible')
        hardware_devices = window.findChild(QObject, 'flightMenuDevices')
        assert hardware_devices is not None and not hardware_devices.property('enabled')
        edit = window.findChild(QObject, 'flightMenuOsdSettings')
        assert edit is not None and edit.property('enabled')
        edit.clicked.emit()
        app.processEvents()
        popup = window.findChild(QObject, 'osdSettingsPopup')
        assert popup is not None and popup.property('visible')
        preview_osd = popup.findChild(QObject, 'osdPreviewOverlay')
        assert preview_osd is not None and preview_osd.property('editing')
        lock_notice = popup.findChild(QObject, 'osd-editing-locked')
        assert lock_notice is not None and not lock_notice.property('visible')
        popup.close()
        app.processEvents()
        close = window.findChild(QObject, 'exitSimulation')
        assert close is not None
        close.clicked.emit()
        app.processEvents()
        assert window.property('simulation') is False
        assert value_map(window.property('t')) == before
        (test_root / 'simulation-tested').write_text('ok')
    return original_single_shot(delay, verify)
QTimer.singleShot = single_shot
import main
sys.argv = ['main.py', '--first-run-acceptance-smoke']
assert main.main() == 0
assert (test_root / 'simulation-tested').is_file(), 'simulation interaction did not complete'
"""
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, QT_QPA_PLATFORM="offscreen", LOCALAPPDATA=temp)
            result = subprocess.run(
                [sys.executable, "-c", script, temp],
                cwd=str(Path(__file__).parent),
                capture_output=True, text=True, env=env, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
