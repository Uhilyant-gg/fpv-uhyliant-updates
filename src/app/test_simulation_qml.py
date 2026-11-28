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
        for action in ('devices', 'vehicles', 'station', 'service'):
            assert find_item(drawer, 'menu-' + action) is not None, action
        button = window.findChild(QObject, 'emptyOpenSimulation')
        assert button is not None, [(child.objectName(), child.metaObject().className()) for child in drawer.childItems()]
        button.clicked.emit()
        app.processEvents()
        assert window.property('simulation') is True
        assert window.findChild(QObject, 'mainPages').property('currentIndex') == 1
        scene = window.findChild(QObject, 'simulationWorld')
        video = window.findChild(QObject, 'mainFlightVideoOutput')
        assert scene is not None and scene.property('visible')
        assert video is not None and not video.property('visible')
        lazy_panels = {
            'streamsPopup': 'streamsContent',
            'timelinePopup': 'timelineContent',
            'backupPopup': 'backupContent',
            'osdSettingsPopup': 'osdSettingsLoader',
            'preflightPopup': 'preflightContent',
            'diagnostics': 'diagnosticsContent',
            'firmwarePopup': 'firmwarePanelLoader',
            'hardwareE2EPopup': 'hardwareE2EContent',
            'updatePopup': 'updateContent',
            'devices': 'devicesContent',
            'recordingPopup': 'recordingContent',
        }
        popups = {}
        for popup_name, loader_name in lazy_panels.items():
            popup = window.findChild(QObject, popup_name)
            loader = window.findChild(QObject, loader_name)
            assert popup is not None and loader is not None, (popup_name, loader_name)
            assert not loader.property('active'), (popup_name, loader.property('active'))
            popups[popup_name] = (popup, loader)
        popup, _ = popups['osdSettingsPopup']
        assert popup.findChild(QObject, 'osdPreviewOverlay') is None
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
        content = window.findChild(QObject, 'flightMenuContent')
        assert content is not None and content.property('width') <= menu.property('width'), 'flight menu content fits the menu'
        hardware_devices = window.findChild(QObject, 'flightMenuDevices')
        assert hardware_devices is not None and not hardware_devices.property('enabled')
        flight_video = window.findChild(QObject, 'mainFlightVideoOutput')
        assert attached_sinks and isinstance(attached_sinks[-1], dvr_runtime.QVideoSink)
        assert attached_sinks[-1] == flight_video.property('videoSink'), 'recording follows the flight video'
        dvr_button = window.findChild(QObject, 'dvrToggle')
        assert dvr_button is not None and not dvr_button.property('visible'), 'no recording of the simulation'
        flight_bar = window.findChild(QObject, 'flightBar')
        assert flight_bar is not None and flight_bar.property('visible')
        video_area = window.findChild(QObject, 'flightVideoArea')
        assert video_area.property('y') >= flight_bar.property('height') > 0, 'video starts below the bar'
        assert window.findChild(QObject, 'flightMenuRecordingSettings') is not None
        edit = window.findChild(QObject, 'flightMenuOsdSettings')
        assert edit is not None and edit.property('enabled')
        edit.clicked.emit()
        app.processEvents()
        assert popup.property('visible')
        preview_osd = popup.findChild(QObject, 'osdPreviewOverlay')
        assert preview_osd is not None and preview_osd.property('editing')
        lock_notice = popup.findChild(QObject, 'osd-editing-locked')
        assert lock_notice is not None and not lock_notice.property('visible')
        popup.close()
        app.processEvents()
        for popup_name, (panel_popup, loader) in popups.items():
            if popup_name == 'osdSettingsPopup':
                continue
            panel_popup.open()
            app.processEvents()
            assert loader.property('active') and loader.property('item') is not None, popup_name
            panel_popup.close()
            app.processEvents()
        from PySide6.QtCore import QMetaObject, Q_ARG
        hubs = {
            'openStationSettings': ('stationSettingsPopup', ('controller', 'recording', 'zerotier', 'backup')),
            'openVehicleSettings': ('vehicleSettingsPopup', ('presets', 'osd')),
            'openService': ('servicePopup', ('diagnostics', 'timeline', 'firmware')),
        }
        hub_loaders = {
            'stationSettingsPopup': 'stationSettingsContent',
            'vehicleSettingsPopup': 'vehicleSettingsContent',
            'servicePopup': 'serviceContent',
        }
        for function, (popup_name, keys) in hubs.items():
            for key in keys:
                QMetaObject.invokeMethod(window, function, Q_ARG('QVariant', key))
                app.processEvents()
                hub_popup = window.findChild(QObject, popup_name)
                assert hub_popup.property('visible'), (popup_name, key)
                page = hub_popup.findChild(QObject, 'hubPage')
                assert page is not None and page.property('item') is not None, (popup_name, key)
                hub = hub_popup.findChild(QObject, 'tabbedHub')
                assert hub is not None and hub.property('currentKey') == key, (popup_name, key)
                tab = find_item(hub, 'hubTab-' + key)
                assert tab is not None and tab.property('checked'), (popup_name, key)
            hub_popup.close()
            app.processEvents()
            assert not window.findChild(QObject, hub_loaders[popup_name]).property('active'), 'closing a section releases its pages'
        close = window.findChild(QObject, 'exitSimulation')
        assert close is not None
        close.clicked.emit()
        app.processEvents()
        assert window.property('simulation') is False
        assert value_map(window.property('t')) == before
        (test_root / 'simulation-tested').write_text('ok')
    return original_single_shot(delay, verify)
QTimer.singleShot = single_shot
import dvr_runtime
attached_sinks = []
original_set_sink = dvr_runtime.DvrRuntime.setVideoSink
def record_sink(self, sink):
    attached_sinks.append(sink)
    return original_set_sink(self, sink)
dvr_runtime.DvrRuntime.setVideoSink = record_sink
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
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
