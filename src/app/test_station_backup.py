import json, tempfile, unittest
from pathlib import Path
from station_backup import StationBackup


class Devices:
    def __init__(self):
        self.snapshot = {
            'devices': [{'id': 'camera'}],
            'streams': [],
            'videoProfiles': [],
            'openipcIdentities': [],
            'activeDeviceId': 'camera',
        }
        self.restored = None

    def exportSnapshot(self):
        return self.snapshot

    def validateSnapshot(self, value):
        return isinstance(value, dict) and set(value) == {
            'devices',
            'streams',
            'videoProfiles',
            'openipcIdentities',
            'activeDeviceId',
        }

    def restoreSnapshot(self, value):
        self.restored = value
        return True


class Tests(unittest.TestCase):
    def test_aes_gcm_export_hides_plaintext_and_declares_cipher(self):
        with tempfile.TemporaryDirectory() as t:
            d = Devices()
            b = StationBackup(d)
            p = Path(t) / 'backup.fub'
            self.assertTrue(b.exportEncrypted(str(p), 'correct horse'))
            raw = p.read_text()
            envelope = json.loads(raw)
            self.assertNotIn('camera', raw)
            self.assertEqual(envelope['version'], 3)
            self.assertEqual(envelope['cipher'], 'aes-256-gcm')
            self.assertNotIn('mac', envelope)

    def test_inspect_requires_correct_password_and_does_not_restore(self):
        with tempfile.TemporaryDirectory() as t:
            d = Devices()
            b = StationBackup(d)
            p = Path(t) / 'backup.fub'
            b.exportEncrypted(str(p), 'correct horse')
            self.assertEqual(b.inspectEncryptedImport(str(p), 'wrong password'), {})
            self.assertIsNone(d.restored)
            plan = b.inspectEncryptedImport(str(p), 'correct horse')
            self.assertEqual(plan['execution'], 'explicit-confirmation-required')
            self.assertEqual(plan['cipher'], 'aes-256-gcm')
            self.assertIsNone(d.restored)

    def test_restore_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as t:
            d = Devices()
            b = StationBackup(d)
            p = Path(t) / 'backup.fub'
            b.exportEncrypted(str(p), 'correct horse')
            b.inspectEncryptedImport(str(p), 'correct horse')
            self.assertFalse(b.restoreInspected(False))
            self.assertIsNone(d.restored)
            b.inspectEncryptedImport(str(p), 'correct horse')
            self.assertTrue(b.restoreInspected(True))
            self.assertIsNotNone(d.restored)

    def test_ciphertext_and_authenticated_metadata_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            for field, value in [('ciphertext', None), ('nonce', 'AAAAAAAAAAAAAAAA')]:
                d = Devices()
                b = StationBackup(d)
                p = Path(t) / (field + '.fub')
                b.exportEncrypted(str(p), 'correct horse')
                raw = json.loads(p.read_text())
                raw[field] = (raw[field][:-4] + 'AAAA') if value is None else value
                p.write_text(json.dumps(raw))
                self.assertEqual(b.inspectEncryptedImport(str(p), 'correct horse'), {})

    def test_weak_password_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertFalse(StationBackup(Devices()).exportEncrypted(str(Path(t) / 'x.fub'), 'short'))

    def test_export_failure_is_human_and_hides_filesystem_error(self):
        with tempfile.TemporaryDirectory() as t:
            blocked = Path(t) / 'not-a-folder'
            blocked.write_text('file', encoding='utf-8')
            backup = StationBackup(Devices())
            self.assertFalse(backup.exportEncrypted(str(blocked / 'backup.fub'), 'correct horse'))
            self.assertIn('Перевірте доступ', backup.result['reason'])
            self.assertNotIn(str(blocked), backup.result['reason'])
            self.assertNotIn('Backup export failed', backup.result['reason'])


if __name__ == '__main__':
    unittest.main()
