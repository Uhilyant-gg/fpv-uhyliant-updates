"""Full app: a camera card enables "Fly" only after a reachable connection type is chosen."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = r"""
import json, sqlite3, sys, time
from pathlib import Path
from PySide6.QtCore import QObject, QSettings, QTimer
from PySide6.QtGui import QGuiApplication

root = Path(sys.argv[1])
db = root / 'FPV-Uhyliant' / 'station.db'
db.parent.mkdir(parents=True)
c = sqlite3.connect(db)
c.execute('CREATE TABLE devices(id TEXT PRIMARY KEY,name TEXT NOT NULL,type TEXT NOT NULL,host TEXT NOT NULL,port INTEGER NOT NULL,connection TEXT NOT NULL,notes TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 0,identity_json TEXT NOT NULL DEFAULT "{}",last_observed_at INTEGER NOT NULL DEFAULT 0)')
c.execute('CREATE TABLE streams(id TEXT PRIMARY KEY,device_id TEXT NOT NULL,name TEXT NOT NULL,kind TEXT NOT NULL,port INTEGER NOT NULL,path TEXT NOT NULL,protocol TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1)')
c.execute('INSERT INTO devices VALUES(?,?,?,?,?,?,?,?,?,?)', ('c1', 'Квадрик', 'OpenIPC', '192.168.1.10', 80, 'Network', '', 0, json.dumps({'onboardingState': 'ready'}), 0))
c.execute('INSERT INTO streams VALUES(?,?,?,?,?,?,?,?)', ('s1', 'c1', 'Основний', 'main', 554, '/stream=0', 'rtsp', 1))
c.commit(); c.close()

import backend, updater_engine, connections_runtime
original_station = backend.Station
backend.Station = lambda: original_station(QSettings(str(root / 'settings.ini'), QSettings.IniFormat))
updater_engine.Updater.check = lambda self: None
reachable = {'192.168.1.10': 7, '2001:db8::10': 55}
runtimes = []
original_init = connections_runtime.ConnectionsRuntime.__init__
def init(self, *args, **kwargs):
    kwargs['prober'] = lambda host, port: reachable.get(host)
    kwargs['run_async'] = False
    original_init(self, *args, **kwargs)
    runtimes.append(self)
connections_runtime.ConnectionsRuntime.__init__ = init

def find_all(item, name, found):
    if item.objectName() == name:
        found.append(item)
    for child in item.childItems():
        find_all(child, name, found)
    return found

def one(window, name):
    items = find_all(window.contentItem(), name, [])
    assert len(items) == 1, (name, len(items))
    return items[0]

original_single_shot = QTimer.singleShot
def single_shot(delay, callback):
    name = getattr(callback, '__name__', '')
    if name == 'quit' and delay == 0:
        return
    if name != 'show_home':
        return original_single_shot(delay, callback)
    def verify():
        callback()
        app = QGuiApplication.instance()
        window = next(w for w in app.topLevelWindows() if w.property('simulation') is not None)
        app.processEvents()
        runtime = runtimes[0]
        runtime.refresh()
        app.processEvents()
        fly = one(window, 'cameraFly')
        assert not fly.property('enabled'), 'no connection chosen yet'
        one(window, 'connection-cloud')
        assert not one(window, 'connection-cloud').property('enabled'), 'cloud needs a server'
        one(window, 'connection-local').clicked.emit()
        app.processEvents()
        assert runtime.selected == {'c1': 'local'}
        assert fly.property('enabled'), 'reachable local connection enables Fly'

        reachable.pop('192.168.1.10')
        runtime.refresh()
        app.processEvents()
        assert not fly.property('enabled'), 'unreachable selection disables Fly'

        one(window, 'connection-starlink').clicked.emit()
        app.processEvents()
        popup = window.findChild(QObject, 'connectionAddressPopup')
        assert popup.property('visible'), 'an address is asked for first'
        field = window.findChild(QObject, 'connectionAddressField')
        field.setProperty('text', 'not an address')
        window.findChild(QObject, 'connectionAddressSave').clicked.emit()
        app.processEvents()
        assert popup.property('visible')
        assert window.findChild(QObject, 'connectionAddressError').property('text') != ''
        field.setProperty('text', '2001:db8::10')
        window.findChild(QObject, 'connectionAddressSave').clicked.emit()
        app.processEvents()
        assert not popup.property('visible')
        assert runtime.selected == {'c1': 'starlink'}
        assert fly.property('enabled')
        assert json.loads((root / 'FPV-Uhyliant' / 'connections.json').read_text()) == {'c1': {'starlink': '2001:db8::10'}}
        (root / 'home-connection-tested').write_text('ok')
        app.quit()
    return original_single_shot(delay, verify)
QTimer.singleShot = single_shot
import main
sys.argv = ['main.py', '--first-run-acceptance-smoke']
main.main()
assert (root / 'home-connection-tested').is_file(), 'interaction did not complete'
print('ok')
"""


def test_fly_needs_a_reachable_connection_choice():
    with tempfile.TemporaryDirectory() as temp:
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", LOCALAPPDATA=temp)
        result = subprocess.run(
            [sys.executable, "-c", SCRIPT, temp],
            cwd=str(Path(__file__).parent),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
