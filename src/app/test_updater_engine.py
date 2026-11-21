import hashlib,json,tempfile,unittest
from pathlib import Path
import updater_engine
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.original=updater_engine.UP;updater_engine.UP=self.root;self.payload=self.root/'package.zip';self.payload.write_bytes(b'payload');self.digest=hashlib.sha256(b'payload').hexdigest();self.manifest={'version':'2.0.11','package':{'file':'package.zip','sha256':self.digest}};(self.root/'ready.json').write_text(json.dumps({'version':'2.0.11','package':str(self.payload),'sha256':self.digest}),encoding='utf-8')
 def tearDown(self):updater_engine.UP=self.original;self.temp.cleanup()
 def test_ready_state_binds_version_file_and_digest(self):
  ready=updater_engine.load_ready(self.manifest);self.assertEqual(ready['version'],'2.0.11');self.assertEqual(ready['sha256'],self.digest)
 def test_rejects_changed_package_after_download(self):
  self.payload.write_bytes(b'tampered');self.assertRaises(RuntimeError,updater_engine.load_ready,self.manifest)
 def test_rejects_manifest_version_or_digest_mismatch(self):
  bad=dict(self.manifest);bad['version']='2.0.12';self.assertRaises(RuntimeError,updater_engine.load_ready,bad)
  bad={'version':'2.0.11','package':{'file':'package.zip','sha256':'0'*64}};self.assertRaises(RuntimeError,updater_engine.load_ready,bad)
 def test_rejects_extra_ready_fields(self):
  payload={'version':'2.0.11','package':str(self.payload),'sha256':self.digest,'trusted':True};(self.root/'ready.json').write_text(json.dumps(payload));self.assertRaises(RuntimeError,updater_engine.load_ready,self.manifest)
if __name__=='__main__':unittest.main()
