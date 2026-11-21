from pathlib import Path

main = Path("src/app/main.py")
source = main.read_text(encoding="utf-8")
replacements = (
    (
        "from PySide6.QtCore import QUrl,QTimer,qInstallMessageHandler",
        "from PySide6.QtCore import QUrl,QTimer",
    ),
    (
        "harness.mark('qgui-application-begin');qInstallMessageHandler(qt_message);app=QGuiApplication(sys.argv);app.setApplicationName('FPV-Uhyliant');app.setApplicationVersion(VERSION);harness.mark('qgui-application-complete')",
        "harness.mark('qgui-application-begin');app=QGuiApplication(sys.argv);app.setApplicationName('FPV-Uhyliant');app.setApplicationVersion(VERSION);harness.mark('qgui-application-complete')",
    ),
    (
        "hardware_e2e=HardwareE2ERuntime(d,diag,credentials);harness.mark('application-objects-complete')",
        "hardware_e2e=HardwareE2ERuntime(d,diag,credentials);app._runtime_refs=(e,s,d,video,v,secondary,streams,fw,acquisition,fwexec,fwsession,credentials,presets,presetexec,links,backup,pairing,telemetry,vehicle,u,diag_events,diag,hardware_e2e,m,msp,crsf,msp_serial,crsf_serial);harness.mark('application-objects-complete')",
    ),
)
for old, new in replacements:
    if old not in source:
        raise SystemExit(f"required startup pattern not found: {old[:100]}")
    source = source.replace(old, new, 1)
main.write_text(source, encoding="utf-8")

Path("src/app/test_windows_qml_startup_crash_policy.py").write_text(
    '''from pathlib import Path


def _source():
    return Path(__file__).with_name("main.py").read_text(encoding="utf-8")


def test_no_python_qt_message_handler_during_qml_load():
    assert "qInstallMessageHandler" not in _source()


def test_qml_runtime_objects_have_process_lifetime():
    source = _source()
    assert "app._runtime_refs=" in source
    refs = source.split("app._runtime_refs=", 1)[1]
    for name in ("video", "streams", "telemetry", "diag", "hardware_e2e"):
        assert name in refs
''',
    encoding="utf-8",
)
