import json,tempfile,unittest
from pathlib import Path
from station_backup import StationBackup
class Devices:
 def __init__(self):self.snapshot={'devices':[{'id':'camera'}],'streams':[],'videoProfiles':[],'openipcIdentities':[],'activeDeviceId':'camera'}
 def exportSnapshot(self):return self.snapshot
 def validateSnapshot(self,value):return isinstance(value,dict) and set(value)=={'devices','streams','videoProfiles','openipcIdentities','activeDeviceId'}
class Tests(unittest.TestCase):
 def test_export_and_inspect_are_versioned_and_non_mutating(self):
  with tempfile.TemporaryDirectory() as t:
   d=Devices();b=StationBackup(d);p=str(Path(t)/'backup.json');self.assertTrue(b.exportTo(p));before=json.loads(json.dumps(d.snapshot));plan=b.inspectImport(p);self.assertEqual(plan['version'],1);self.assertEqual(plan['execution'],'explicit-user-decision-required');self.assertEqual(d.snapshot,before)
 def test_tampered_payload_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   d=Devices();b=StationBackup(d);p=Path(t)/'backup.json';b.exportTo(str(p));raw=json.loads(p.read_text());raw['payload']['devices']['activeDeviceId']='other';p.write_text(json.dumps(raw));self.assertEqual(b.inspectImport(str(p)),{})
 def test_invalid_schema_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'bad.json';p.write_text('{"payload":{"schema":"other"},"sha256":"x"}');self.assertEqual(StationBackup(Devices()).inspectImport(str(p)),{})
if __name__=='__main__':unittest.main()
