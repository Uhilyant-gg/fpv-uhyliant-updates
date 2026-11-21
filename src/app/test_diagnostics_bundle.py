import json,tempfile,unittest
from pathlib import Path
from diagnostics_bundle import diagnostic_bundle,export_bundle

class Tests(unittest.TestCase):
 def test_bundle_preserves_unknowns_and_has_identity(self):
  b=diagnostic_bundle('2.0.12',devices=[{'firmware':None}],now=42,correlation_id='cid')
  self.assertEqual(b['schemaVersion'],1);self.assertEqual(b['correlationId'],'cid');self.assertEqual(b['generatedAt'],42);self.assertIsNone(b['devices'][0]['firmware'])
 def test_secrets_are_redacted_recursively(self):
  b=diagnostic_bundle('2.0.12',devices=[{'password':'p','nested':{'token':'t','sensor':'imx335'}}],protocols={'authorization':'x'})
  self.assertEqual(b['devices'][0]['password'],'[redacted]');self.assertEqual(b['devices'][0]['nested']['token'],'[redacted]');self.assertEqual(b['devices'][0]['nested']['sensor'],'imx335');self.assertEqual(b['protocols']['authorization'],'[redacted]')
 def test_secret_key_variants_and_private_signing_material_are_redacted(self):
  b=diagnostic_bundle('2.0.12',devices=[{'cameraPassword':'p','ssh_private_key':'ssh','access-token':'tok'}],updater={'releaseSigningKey':'sign','publicKey':'public'})
  d=b['devices'][0];self.assertEqual(d['cameraPassword'],'[redacted]');self.assertEqual(d['ssh_private_key'],'[redacted]');self.assertEqual(d['access-token'],'[redacted]');self.assertEqual(b['updater']['releaseSigningKey'],'[redacted]');self.assertEqual(b['updater']['publicKey'],'public')
 def test_secret_values_embedded_in_strings_are_redacted(self):
  b=diagnostic_bundle('2.0.12',events=[{'message':'request failed Authorization: Bearer abc123','detail':'password=hunter2 host=192.168.1.50'}])
  event=b['events'][0];self.assertNotIn('abc123',event['message']);self.assertIn('Bearer [redacted]',event['message']);self.assertNotIn('hunter2',event['detail']);self.assertIn('password=[redacted]',event['detail'])
 def test_recent_events_are_bounded(self):
  b=diagnostic_bundle('2.0.12',events=[{'n':i} for i in range(150)])
  self.assertEqual(len(b['events']),100);self.assertEqual(b['events'][0]['n'],50)
 def test_export_is_json_and_sanitizes_again(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'diagnostics.json';export_bundle(p,{'password':'secret','message':'token=plain-text-token','ok':True});data=json.loads(p.read_text(encoding='utf-8'));self.assertEqual(data['password'],'[redacted]');self.assertEqual(data['message'],'token=[redacted]');self.assertTrue(data['ok'])
if __name__=='__main__':unittest.main()
