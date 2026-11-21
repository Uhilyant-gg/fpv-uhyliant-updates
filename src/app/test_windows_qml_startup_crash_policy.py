from pathlib import Path


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
