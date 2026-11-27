import gc
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QSettings
import devices as devices_module
from automatic_backup import AutomaticBackup, MISSING_KEY
from backend import Station
from devices_routeaware import Devices
from station_backup import StationBackup


class Store:
    def __init__(self):
        self.data = {}

    def put(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)


class AutomaticBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_data, self.old_db = devices_module.DATA, devices_module.DB
        devices_module.DATA = self.root
        devices_module.DB = self.root / 'station.db'
        self.devices = Devices()
        self.station = Station(QSettings(str(self.root / 'settings.ini'), QSettings.IniFormat))
        self.store = Store()
        self.auto = AutomaticBackup(self.root / 'automatic', self.store, self.devices, self.station)
        self.backup = StationBackup(self.devices, self.auto)
        self.did = self.devices.addDevice('Camera', 'Camera', '192.168.1.40', 80, 'Network', '')

    def tearDown(self):
        devices_module.DATA, devices_module.DB = self.old_data, self.old_db
        gc.collect()
        self.temp.cleanup()

    def test_update_snapshot_is_encrypted_and_captures_prechange_osd(self):
        self.station.setOSDStyle(0.7, 1.2)
        self.station.setOSDPosition('bottom-right')
        before = self.devices.exportSnapshot()
        self.assertTrue(self.devices.updateDevice(self.did, 'New name', '192.168.1.41', 81, ''))
        snapshot = self.auto.latest()
        self.assertEqual(snapshot['devices'], before)
        self.assertEqual(snapshot['osd'], {'enabled': True, 'opacity': 0.7, 'scale': 1.2, 'position': 'bottom-right'})
        files = list(self.auto.path.glob('snapshot-*.fub'))
        self.assertEqual(len(files), 1)
        self.assertNotIn('192.168.1.40', files[0].read_text())
        self.assertNotIn('bottom-right', files[0].read_text())

    def test_restore_needs_confirmation_and_first_saves_current_state(self):
        self.devices.removeDevice(self.did)
        self.assertEqual(self.devices.count, 0)
        self.assertTrue(self.backup.inspectAutomatic())
        self.assertFalse(self.backup.restoreInspected(False))
        self.assertEqual(self.devices.count, 0)
        self.assertTrue(self.backup.restoreInspected(True))
        self.assertEqual(self.devices.count, 1)
        self.assertEqual(self.auto.latest()['devices']['devices'], [])
        self.assertEqual(len(list(self.auto.path.glob('snapshot-*.fub'))), 2)

    def test_missing_key_blocks_mutation_without_replacing_key_or_snapshot(self):
        self.devices.removeDevice(self.did)
        files = list(self.auto.path.glob('snapshot-*.fub'))
        content = files[0].read_bytes()
        self.store.data.clear()
        notices = []
        self.backup.automaticFailure.connect(notices.append)
        plan = self.backup.inspectAutomatic()
        self.assertFalse(plan)
        self.assertEqual(notices[-1], MISSING_KEY)
        new_id = self.devices.addDevice('New', 'Camera', '192.168.1.42', 80, 'Network', '')
        self.devices.removeDevice(new_id)
        self.assertEqual(self.devices.count, 1)
        self.assertEqual(notices[-1], MISSING_KEY)
        self.assertFalse(self.backup.inspectEncryptedImport('missing.fub', 'password'))
        self.assertFalse(self.auto.create())
        self.assertEqual(self.auto.error, MISSING_KEY)
        self.assertEqual(self.store.data, {})
        self.assertEqual(files[0].read_bytes(), content)

    def test_failed_snapshot_prevents_update_delete_and_restore(self):
        stream = self.devices.addStream(self.did, 'Main', 'main', 554, '/stream', 'rtsp')
        before = self.devices.exportSnapshot()
        notices = []
        self.backup.automaticFailure.connect(notices.append)
        with patch.object(self.auto, 'create', return_value=False):
            self.auto.error = 'Snapshot unavailable'
            self.assertFalse(self.devices.updateDevice(self.did, 'Changed', '192.168.1.41', 80, ''))
            self.devices.removeStream(stream)
            self.devices.removeDevice(self.did)
            self.assertFalse(self.devices.restoreSnapshot(before))
        self.assertEqual(self.devices.exportSnapshot(), before)
        self.assertEqual(notices, ['Snapshot unavailable'] * 4)

    def test_tampering_and_wrong_installation_fail_closed(self):
        self.assertTrue(self.auto.create())
        file = next(self.auto.path.glob('snapshot-*.fub'))
        wrapper = json.loads(file.read_text())
        wrapper['installationId'] = '0' * 32
        file.write_text(json.dumps(wrapper))
        self.assertIsNone(self.auto.latest())
        self.assertFalse(self.backup.inspectAutomatic())
        self.assertEqual(self.devices.count, 1)

    def test_invalid_live_state_does_not_create_snapshot(self):
        with patch.object(self.devices, 'exportSnapshot', return_value={'devices': []}):
            self.assertFalse(self.auto.create())
        self.assertFalse(self.auto.path.exists())

    def test_restart_uses_existing_key_and_keeps_user_files(self):
        self.auto.path.mkdir()
        user_file = self.auto.path / 'my-backup.fub'
        user_file.write_text('user data')
        self.assertTrue(self.auto.create())
        keys = dict(self.store.data)
        restarted = AutomaticBackup(self.auto.path, self.store, self.devices, self.station)
        self.assertEqual(restarted.latest()['devices'], self.devices.exportSnapshot())
        self.assertEqual(self.store.data, keys)
        self.assertEqual(user_file.read_text(), 'user data')

    def test_unverified_new_snapshot_never_becomes_recovery_target(self):
        self.assertTrue(self.auto.create())
        before = self.auto.latest()
        with patch.object(self.auto, '_read', side_effect=ValueError('bad snapshot')):
            self.assertFalse(self.auto.create())
        self.assertEqual(self.auto.latest(), before)


if __name__ == '__main__':
    unittest.main()
