import json,tempfile,unittest
from pathlib import Path
from station_backup import StationBackup
class Devices:
 def __init__(self):self.snapshot={'devices':[{'id':'camera'}],'streams':[],'videoProfiles':[],'openipcIdentities':[],'activeDeviceId':'camera'};self.restored=None
 def exportSnapshot(self):return self.snapshot
 def validateSnapshot(self,value):return isinstance(value,dict) and set(value)=={'devices','streams','videoProfiles','openipcIdentities','activeDeviceId'}
 def restoreSnapshot(self,value):self.restored=value;return True
class Tests(unittest.TestCase):
 def test_encrypted_export_does_not_expose_snapshot_plaintext(self):
  with tempfile.TemporaryDirectory() as t:
   d=Devices();b=StationBackup(d);p=Path(t)/'backup.fub';self.assertTrue(b.exportEncrypted(str(p),'correct horse'));raw=p.read_text();self.assertNotIn('camera',raw);self.assertEqual(json.loads(raw)['version'],2)
 def test_inspect_requires_correct_password_and_does_not_restore(self):
  with tempfile.TemporaryDirectory() as t:
   d=Devices();b=StationBackup(d);p=Path(t)/'backup.fub';b.exportEncrypted(str(p),'correct horse');self.assertEqual(b.inspectEncryptedImport(str(p),'wrong password'),{});self.assertIsNone(d.restored);plan=b.inspectEncryptedImport(str(p),'correct horse');self.assertEqual(plan['execution'],'explicit-confirmation-required');self.assertIsNone(d.restored)
 def test_restore_requires_explicit_confirmation(self):
  with tempfile.TemporaryDirectory() as t:
   d=Devices();b=StationBackup(d);p=Path(t)/'backup.fub';b.exportEncrypted(str(p),'correct horse');b.inspectEncryptedImport(str(p),'correct horse');self.assertFalse(b.restoreInspected(False));self.assertIsNone(d.restored);b.inspectEncryptedImport(str(p),'correct horse');self.assertTrue(b.restoreInspected(True));self.assertIsNotNone(d.restored)
 def test_tampered_ciphertext_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   d=Devices();b=StationBackup(d);p=Path(t)/'backup.fub';b.exportEncrypted(str(p),'correct horse');raw=json.loads(p.read_text());raw['ciphertext']=raw['ciphertext'][:-4]+'AAAA';p.write_text(json.dumps(raw));self.assertEqual(b.inspectEncryptedImport(str(p),'correct horse'),{})
if __name__=='__main__':unittest.main()
