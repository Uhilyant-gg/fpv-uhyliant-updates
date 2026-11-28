"""Every ``devicesModel.<name>`` used by QML must exist in the Qt meta-object.

Python tests call model methods directly, so a member missing from the Qt
meta-object (for example after PySide drops a subclass's members) only breaks
the real UI. This test reads the QML and checks the meta-object QML uses.
"""

import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_JS_MEMBERS = {"length", "toString", "valueOf", "connect", "disconnect"}


def _qml_members(model_name):
    names = set()
    for path in HERE.glob("*.qml"):
        for match in re.finditer(r"(?<![\w.])" + model_name + r"\.([A-Za-z_]\w*)", path.read_text(encoding="utf-8")):
            names.add(match.group(1))
    return names - _JS_MEMBERS


def _meta_names(meta):
    names = {meta.property(i).name() for i in range(meta.propertyCount())}
    for i in range(meta.methodCount()):
        names.add(meta.method(i).name().data().decode())
    return names


# QML context property name -> (module, class) as registered in main.py.
MODELS = {
    "station": ("backend", "Station"),
    "homeDashboard": ("backend", "HomeDashboard"),
    "devicesModel": ("devices_routeaware", "Devices"),
    "videoRuntime": ("video", "VideoRuntime"),
    "secondaryVideoRuntime": ("video", "VideoRuntime"),
    "mspSerial": ("serial_telemetry", "MspSerialTransport"),
    "crsfSerial": ("serial_telemetry", "CrsfSerialTransport"),
    "videoWorkspaceRuntime": ("video", "VideoWorkspaceRuntime"),
    "streamWorkspace": ("stream_workspace", "StreamWorkspace"),
    "firmwareCenter": ("firmware_center", "FirmwareCenter"),
    "firmwareAcquisition": ("openipc_firmware_acquisition", "OpenIPCFirmwareAcquisition"),
    "firmwareExecutor": ("firmware_executor", "FirmwareExecutor"),
    "firmwareUpdateSession": ("firmware_update_session", "FirmwareUpdateSession"),
    "cameraCredentials": ("camera_credentials", "CameraCredentials"),
    "cameraPresets": ("camera_presets", "CameraPresets"),
    "cameraPresetExecutor": ("camera_preset_executor", "CameraPresetExecutor"),
    "linkDiagnostics": ("link_diagnostics", "LinkDiagnostics"),
    "stationBackup": ("station_backup", "StationBackup"),
    "pairingRegistry": ("pairing", "PairingRegistry"),
    "mavlinkRuntime": ("mavlink_runtime", "MavlinkRuntime"),
    "telemetryRuntime": ("telemetry_provider", "TelemetryRouter"),
    "vehicleRuntime": ("vehicle", "VehicleRuntime"),
    "timelineRuntime": ("timeline_runtime", "TimelineRuntime"),
    "displayRuntime": ("display_runtime", "DisplayRuntime"),
    "updater": ("updater_engine", "Updater"),
    "diagnosticsRuntime": ("diagnostics_runtime", "DiagnosticsRuntime"),
    "hardwareE2ERuntime": ("hardware_e2e_runtime", "HardwareE2ERuntime"),
    "controllerRuntime": ("controller_runtime", "ControllerRuntime"),
    "flightAlerts": ("flight_alerts_runtime", "FlightAlertsRuntime"),
    "presetsRuntime": ("presets_runtime", "PresetsRuntime"),
    "dvrRuntime": ("dvr_runtime", "DvrRuntime"),
    "linkMonitor": ("link_monitor", "LinkMonitor"),
    "linkDoctor": ("link_doctor", "LinkDoctor"),
    "connectionsRuntime": ("connections_runtime", "ConnectionsRuntime"),
}


class QmlModelBindingTests(unittest.TestCase):
    def test_every_model_member_used_by_qml_is_visible_to_qt(self):
        import importlib

        problems = []
        for name, (module_name, class_name) in sorted(MODELS.items()):
            cls = getattr(importlib.import_module(module_name), class_name)
            missing = sorted(_qml_members(name) - _meta_names(cls.staticMetaObject))
            if missing:
                problems.append(name + ": " + ", ".join(missing))
        self.assertEqual(problems, [], "QML uses members unknown to Qt")

    def test_devices_model_members_used_by_qml_are_visible_to_qt(self):
        import devices_routeaware as module

        meta = module.Devices.staticMetaObject
        missing = sorted(_qml_members("devicesModel") - _meta_names(meta))
        self.assertEqual(missing, [], "QML uses devicesModel members unknown to Qt: " + ", ".join(missing))

    def test_route_aware_signals_are_registered(self):
        import devices_routeaware as module

        meta = module.Devices.staticMetaObject
        for signature in ("manualChanged()", "scanStateChanged()", "firmwarePreparationRequested(QString)"):
            self.assertGreaterEqual(meta.indexOfSignal(signature), 0, signature)


if __name__ == "__main__":
    unittest.main()
