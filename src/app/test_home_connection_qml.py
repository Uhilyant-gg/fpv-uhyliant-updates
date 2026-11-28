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

import backend, updater_engine, connections_runtime, station_backup, traceback
# Changing a camera first makes an automatic backup, which needs the Windows secret store.
station_backup.StationBackup._protect_change = lambda self: True
original_station = backend.Station
backend.Station = lambda: original_station(QSettings(str(root / 'settings.ini'), QSettings.IniFormat))
updater_engine.Updater.check = lambda self: None
reachable = {'192.168.1.10': 7, '2001:db8::10': 55, 'fd80:56c2:e21c:0:199:9389:e92c:eee5': 41}
class FakeZeroTier:
    def snapshot(self):
        return {'service': 'ok', 'nodeId': 'a1b2c3d4e5', 'networks': {'8056c2e21c000001': {'status': 'OK', 'name': ''}},
                'peers': {'89e92ceee5': {'latency': 41, 'direct': True}}}
    def join(self, network):
        return True
runtimes = []
original_init = connections_runtime.ConnectionsRuntime.__init__
def init(self, *args, **kwargs):
    kwargs['prober'] = lambda host, port: reachable.get(host)
    kwargs['run_async'] = False
    kwargs['zerotier'] = FakeZeroTier()
    kwargs['listen'] = False
    kwargs['camera_setup'] = None
    kwargs['camera_inspect'] = None
    kwargs['binder'] = lambda port: {'state': 'grey', 'message': 'сіра адреса'}
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
        try:
            check()
        except Exception:
            traceback.print_exc()
            QGuiApplication.instance().exit(1)
    def check():
        callback()
        app = QGuiApplication.instance()
        window = next(w for w in app.topLevelWindows() if w.property('simulation') is not None)
        app.processEvents()
        runtime = runtimes[0]
        runtime.refresh()
        app.processEvents()
        fly = one(window, 'cameraFly')
        assert not fly.property('enabled'), 'no connection chosen yet'
        assert not one(window, 'connection-static').property('visible'), 'not set up yet: behind "＋"'
        one(window, 'connectionMore').clicked.emit()
        app.processEvents()
        assert one(window, 'connection-static').property('visible')
        one(window, 'connection-static').clicked.emit()
        app.processEvents()
        assert not window.findChild(QObject, 'cameraSettingsDialog').property('visible'), 'no form: the station binds by itself'
        assert runtime.bindStatus['state'] == 'grey'
        assert runtime.statuses['c1']['static']['label'] == 'сіра адреса'

        cloud = one(window, 'connection-cloud')
        assert cloud.property('enabled')
        assert runtime.statuses['c1']['cloud']['label'] == 'вказати мережу'
        cloud.clicked.emit()
        app.processEvents()
        dialog = window.findChild(QObject, 'cameraSettingsDialog')
        assert dialog.property('visible'), 'ZeroTier IDs are asked for in the camera settings'
        window.findChild(QObject, 'cameraZtNetworkField').setProperty('text', '8056c2e21c000001')
        window.findChild(QObject, 'cameraZtNodeField').setProperty('text', 'bad')
        window.findChild(QObject, 'cameraSettingsSave').clicked.emit()
        app.processEvents()
        assert dialog.property('visible') and window.findChild(QObject, 'cameraSettingsError').property('text') != ''
        window.findChild(QObject, 'cameraZtNodeField').setProperty('text', '89e92ceee5')
        window.findChild(QObject, 'cameraSettingsSave').clicked.emit()
        app.processEvents()
        assert not dialog.property('visible')
        assert runtime.statuses['c1']['cloud']['label'] == '41 мс · напряму'
        one(window, 'connection-cloud').clicked.emit()
        app.processEvents()
        assert runtime.selected == {'c1': 'cloud'}
        assert one(window, 'cameraFly').property('enabled'), 'ZeroTier camera is reachable'
        fly = one(window, 'cameraFly')
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
        dialog = window.findChild(QObject, 'cameraSettingsDialog')
        assert dialog.property('visible'), 'an address is asked for first, in the camera settings'
        field = window.findChild(QObject, 'cameraStarlinkField')
        field.setProperty('text', 'not an address')
        window.findChild(QObject, 'cameraSettingsSave').clicked.emit()
        app.processEvents()
        assert dialog.property('visible')
        assert window.findChild(QObject, 'cameraSettingsError').property('text') != ''
        field.setProperty('text', '2001:db8::10')
        window.findChild(QObject, 'cameraNameField').setProperty('text', 'Квадрик 7')
        window.findChild(QObject, 'cameraSettingsSave').clicked.emit()
        app.processEvents()
        assert not dialog.property('visible')
        assert json.loads((root / 'FPV-Uhyliant' / 'connections.json').read_text()) == {
            'c1': {'starlink': '2001:db8::10', 'starlinkSource': 'manual', 'ztNetwork': '8056c2e21c000001',
                   'ztNode': '89e92ceee5', 'ztSource': 'manual', 'pushPort': 5600}}
        names = [d['name'] for d in runtime._devices.items]
        assert names == ['Квадрик 7'], names
        assert runtime.statuses['c1']['starlink']['state'] == 'available'
        one(window, 'connection-starlink').clicked.emit()
        app.processEvents()
        assert runtime.selected == {'c1': 'starlink'}
        assert one(window, 'cameraFly').property('enabled'), 'the renamed card is rebuilt; look it up again'

        one(window, 'cameraSettings').clicked.emit()
        app.processEvents()
        assert dialog.property('visible')
        window.findChild(QObject, 'cameraArchive').clicked.emit()
        app.processEvents()
        assert not dialog.property('visible')
        devices = runtime._devices
        assert devices.homeItems == [] and [d['id'] for d in devices.archivedItems] == ['c1']
        assert find_all(window.contentItem(), 'cameraCard', []) == [], 'archived camera leaves the home screen'
        archive_button = one(window, 'homeArchive')
        assert archive_button.property('text') == 'Архів (1)'
        archive_button.clicked.emit()
        app.processEvents()
        archive = window.findChild(QObject, 'archiveDialog')
        assert archive.property('visible')
        rows = find_all(archive.property('contentItem'), 'archiveRestore', [])
        assert len(rows) == 1
        rows[0].clicked.emit()
        app.processEvents()
        assert [d['id'] for d in devices.homeItems] == ['c1'] and devices.archivedItems == []
        assert len(find_all(window.contentItem(), 'cameraCard', [])) == 1

        devices.archiveDevice('c1')
        app.processEvents()
        find_all(archive.property('contentItem'), 'archiveDelete', [])[0].clicked.emit()
        app.processEvents()
        assert devices.archivedItems != [], 'delete asks for confirmation first'
        find_all(archive.property('contentItem'), 'archiveDeleteConfirm', [])[0].clicked.emit()
        app.processEvents()
        assert devices.items == [], 'camera deleted from the archive'
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
