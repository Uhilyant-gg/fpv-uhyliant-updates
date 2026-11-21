import json,tempfile,unittest
from pathlib import Path
from diagnostics_bundle import diagnostic_bundle,export_bundle
class Tests(unittest.TestCase):
 def test_bundle_preserves_unknowns_and_sanitizes_secrets(self):
  bundle=diagnostic_bundle('2.0',devices=[{'id':'cam','password':'pw'}],events=[{'component':'firmware','correlationId':'cid','message':'Authorization: Bearer abc','detail':{'token':'abc','state':'blocked'}}],now=42,correlation_id='bundle');text=json.dumps(bundle);self.assertNotIn('pw',text);self.assertNotIn('Bearer abc',text);self.assertNotIn('"abc"',text);self.assertEqual(bundle['generatedAt'],42);self.assertEqual(bundle['correlationId'],'bundle');self.assertEqual(bundle['firmwareLifecycle']['correlationId'],'cid');self.assertEqual(bundle['firmwareLifecycle']['state'],'blocked')
 def test_firmware_lifecycle_uses_latest_attempt_only(self):
  events=[{'component':'firmware','correlationId':'old','message':'old','detail':{'state':'error'}},{'component':'video','correlationId':'v','message':'x','detail':None},{'component':'firmware','correlationId':'new','message':'start','detail':{'state':'reboot-pending'}},{'component':'firmware','correlationId':'new','message':'verified','detail':{'state':'verified'}}];bundle=diagnostic_bundle('2.0',events=events,now=1);self.assertEqual(bundle['firmwareLifecycle']['correlationId'],'new');self.assertEqual(bundle['firmwareLifecycle']['state'],'verified');self.assertEqual([x['message'] for x in bundle['firmwareLifecycle']['events']],['start','verified'])
 def test_export_is_atomic_json_and_resanitizes_input(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'bundle.json';export_bundle(path,{'nested':{'password':'secret'},'message':'token=abc'});payload=json.loads(path.read_text(encoding='utf-8'));self.assertEqual(payload['nested']['password'],'[redacted]');self.assertNotIn('token=abc',path.read_text(encoding='utf-8'));self.assertFalse(path.with_suffix('.json.tmp').exists())
if __name__=='__main__':unittest.main()
