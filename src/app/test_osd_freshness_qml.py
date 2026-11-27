import os
from pathlib import Path
import subprocess
import sys
import unittest


class OsdFreshnessQmlTests(unittest.TestCase):
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
