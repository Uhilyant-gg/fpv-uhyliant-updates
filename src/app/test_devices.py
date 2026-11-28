import sqlite3, tempfile, unittest
from contextlib import closing
from pathlib import Path
import devices as devices_module


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        devices_module.DATA = root
        devices_module.DB = root / 'devices.sqlite3'
        devices_module.LEGACY_DB = root / 'devices.json'
        self.orig = devices_module.interfaces
        devices_module.interfaces = lambda: []

    def tearDown(self):
        devices_module.interfaces = self.orig
        self.temp.cleanup()

    def test_snapshot_and_transactional_restore(self):
        d = devices_module.Devices()
        events = []
        d.deviceAdded.connect(lambda: events.append('added'))
        d.deviceRemoved.connect(lambda: events.append('removed'))
        d.deviceListRestored.connect(lambda: events.append('restored'))
        did = d.addDevice('Camera', 'Camera', '192.168.1.40', 80, 'Network', '')
        self.assertEqual(events, ['added'])
        d.setActive(did)
        snap = d.exportSnapshot()
        self.assertTrue(d.validateSnapshot(snap))
        d.removeDevice(did)
        self.assertEqual(d.count, 0)
        self.assertEqual(events, ['added', 'removed'])
        self.assertTrue(d.restoreSnapshot(snap))
        self.assertEqual(d.count, 1)
        self.assertEqual(d.activeName, 'Camera')
        self.assertEqual(d.activeId, did)
        self.assertEqual(events, ['added', 'removed', 'restored'])

    def test_invalid_snapshot_leaves_live_state_unchanged(self):
        d = devices_module.Devices()
        d.addDevice('Camera', 'Camera', '192.168.1.40', 80, 'Network', '')
        before = d.exportSnapshot()
        bad = dict(before)
        bad['activeDeviceId'] = 'missing'
        self.assertFalse(d.restoreSnapshot(bad))
        self.assertEqual(d.exportSnapshot(), before)

    def test_failed_transaction_rolls_back(self):
        d = devices_module.Devices()
        d.addDevice('Camera', 'Camera', '192.168.1.40', 80, 'Network', '')
        before = d.exportSnapshot()
        bad = {k: (list(v) if isinstance(v, list) else v) for k, v in before.items()}
        bad['devices'] = [dict(bad['devices'][0])]
        bad['devices'][0]['port'] = 'not-int'
        self.assertTrue(d.validateSnapshot(bad))
        self.assertFalse(d.restoreSnapshot(bad))
        self.assertEqual(d.exportSnapshot(), before)

    def test_observation_is_persisted_but_reset_by_snapshot_restore(self):
        d = devices_module.Devices()
        did = d.addDevice('Camera', 'OpenIPC', '192.168.1.40', 80, 'Network', '')
        d._save_identity(did, {'verified': True, 'firmware': 'v1'})
        d._load()
        self.assertEqual(d.items[0]['versionLabel'], 'v1')
        self.assertEqual(d.items[0]['lastObservedAt'], 0)
        self.assertTrue(d.markObserved('192.168.1.40'))
        self.assertGreater(d.items[0]['lastObservedAt'], 0)
        snapshot = d.exportSnapshot()
        self.assertNotIn('lastObservedAt', snapshot['devices'][0])
        self.assertTrue(d.restoreSnapshot(snapshot))
        self.assertEqual(d.items[0]['lastObservedAt'], 0)

    def test_existing_database_adds_observation_column_without_losing_devices(self):
        with closing(sqlite3.connect(devices_module.DB)) as db:
            with db:
                db.execute(
                    'CREATE TABLE devices(id TEXT PRIMARY KEY,name TEXT NOT NULL,type TEXT NOT NULL,host TEXT NOT NULL,port INTEGER NOT NULL,connection TEXT NOT NULL,notes TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 0,identity_json TEXT NOT NULL DEFAULT "{}")'
                )
                db.execute(
                    "INSERT INTO devices(id,name,type,host,port,connection,notes,active,identity_json) VALUES('saved','Camera','OpenIPC','192.168.1.40',80,'Network','',0,'{}')"
                )
        d = devices_module.Devices()
        self.assertEqual(d.count, 1)
        self.assertEqual(d.items[0]['id'], 'saved')
        self.assertEqual(d.items[0]['lastObservedAt'], 0)

    def test_connection_closes_after_commit_and_rollback(self):
        d = devices_module.Devices()
        with d._connect() as db:
            db.execute(
                "INSERT INTO devices(id,name,type,host,port,connection,notes) VALUES('one','Camera','OpenIPC','192.168.1.40',80,'Network','')"
            )
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute('SELECT 1')
        with self.assertRaisesRegex(ValueError, 'rollback'):
            with d._connect() as failed:
                failed.execute("DELETE FROM devices WHERE id='one'")
                raise ValueError('rollback')
        with self.assertRaises(sqlite3.ProgrammingError):
            failed.execute('SELECT 1')
        d._load()
        self.assertEqual(d.count, 1)


if __name__ == '__main__':
    unittest.main()
