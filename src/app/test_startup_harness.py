import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from startup_harness import StartupHarness,run_import_probes
class Tests(unittest.TestCase):
 def test_markers_are_append_only_and_latest_is_atomic(self):
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/'stages.jsonl';h=StartupHarness(path,'2.0.x');h.mark('one');h.mark('two')
   rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
   self.assertEqual(['one','two'],[row['stage'] for row in rows]);self.assertEqual('two',json.loads(h.latest.read_text(encoding='utf-8'))['stage'])
 def test_import_probe_records_boundary_before_failure(self):
  with tempfile.TemporaryDirectory() as root:
   h=StartupHarness(Path(root)/'stages.jsonl','2.0.x')
   with patch('startup_harness.PROBES',(('python-runtime',None),('broken','missing_test_module'))):
    with self.assertRaises(ModuleNotFoundError):run_import_probes(h)
   stages=[json.loads(line)['stage'] for line in h.path.read_text(encoding='utf-8').splitlines()]
   self.assertEqual(['probe-start','python-runtime-begin','python-runtime-complete','broken-begin'],stages)
if __name__=='__main__':unittest.main()
