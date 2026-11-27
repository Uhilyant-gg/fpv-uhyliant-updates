import importlib, json, os, platform, sys, time, traceback
from pathlib import Path
from startup_acceptance import read_startup_acceptance  # noqa: F401 - re-exported for main.py

PROBES = (
    ('python-runtime', None),
    ('pyside-core', 'PySide6.QtCore'),
    ('pyside-gui', 'PySide6.QtGui'),
    ('pyside-qml', 'PySide6.QtQml'),
    ('pyside-quick', 'PySide6.QtQuick'),
    ('pyside-controls', 'PySide6.QtQuickControls2'),
    ('pyside-multimedia', 'PySide6.QtMultimedia'),
    ('pyside-serial', 'PySide6.QtSerialPort'),
    ('pymavlink', 'pymavlink.mavutil'),
    ('paramiko', 'paramiko'),
)


class StartupHarness:
    def __init__(self, path, version, started_at=None):
        self.path = Path(path)
        self.version = version
        self.started = time.monotonic() if started_at is None else started_at
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.latest = self.path.with_suffix('.latest.json')

    def mark(self, stage, status='ok', detail=None):
        payload = {
            'stage': stage,
            'status': status,
            'version': self.version,
            'pid': os.getpid(),
            'timestamp': time.time(),
            'elapsedMs': round((time.monotonic() - self.started) * 1000),
            'frozen': bool(getattr(sys, 'frozen', False)),
        }
        if detail is not None:
            payload['detail'] = detail
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n')
            f.flush()
            os.fsync(f.fileno())
        tmp = self.latest.with_suffix(self.latest.suffix + '.tmp')
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, self.latest)
        return payload

    def failed(self, stage, exc):
        return self.mark(
            stage, 'error', {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        )


def default_path(data):
    return Path(data) / 'startup-stages.jsonl'


def run_import_probes(harness):
    harness.mark(
        'probe-start', detail={'python': sys.version, 'platform': platform.platform(), 'executable': sys.executable}
    )
    for stage, module in PROBES:
        harness.mark(stage + '-begin')
        if module:
            importlib.import_module(module)
        harness.mark(stage + '-complete')
    harness.mark('probe-complete')
    return 0


def run_qt_probe(harness, argv):
    harness.mark('qt-application-begin')
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication(argv)
    harness.mark('qt-application-complete')
    from PySide6.QtQml import QQmlApplicationEngine

    harness.mark('qml-engine-begin')
    engine = QQmlApplicationEngine()
    harness.mark('qml-engine-complete')
    app.processEvents()
    harness.mark('event-processing-complete')
    del engine
    return 0
