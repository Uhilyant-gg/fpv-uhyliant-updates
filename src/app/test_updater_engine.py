import hashlib,json,tempfile,unittest
from pathlib import Path
import updater_engine
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.original=updater_engine.UP;updater_engine.UP=self.root;self.payload=self.root/'package.zip';self.payload.write_bytes(b'payload');self.digest=hashlib.sha256(b'payload').hexdigest();self.manifest={'version':'2.0.11','package':{'file':'package.zip','sha256':self.digest}};(self.root/'ready.json').write_text(json.dumps({'version':'2.0.11','package':str(self.payload),'sha256':self.digest}),encoding='utf-8')
 def tearDown(self):updater_engine.UP=self.original;self.temp.cleanup()
 def test_ready_state_binds_version_file_and_digest(self):self.assertEqual(updater_engine.load_ready(self.manifest)['sha256'],self.digest)
 def test_rejects_changed_package_after_download(self):self.payload.write_bytes(b'tampered');self.assertRaises(RuntimeError,updater_engine.load_ready,self.manifest)
 def test_rejects_manifest_version_or_digest_mismatch(self):
  bad=dict(self.manifest);bad['version']='2.0.12';self.assertRaises(RuntimeError,updater_engine.load_ready,bad);bad={'version':'2.0.11','package':{'file':'package.zip','sha256':'0'*64}};self.assertRaises(RuntimeError,updater_engine.load_ready,bad)
 def test_rejects_extra_ready_fields(self):
  (self.root/'ready.json').write_text(json.dumps({'version':'2.0.11','package':str(self.payload),'sha256':self.digest,'trusted':True}));self.assertRaises(RuntimeError,updater_engine.load_ready,self.manifest)
 def test_rejects_ready_package_outside_updates_directory(self):
  outside=self.root.parent/(self.root.name+'-outside.zip');outside.write_bytes(b'payload')
  try:
   (self.root/'ready.json').write_text(json.dumps({'version':'2.0.11','package':str(outside),'sha256':self.digest}),encoding='utf-8');self.assertRaises(RuntimeError,updater_engine.load_ready,self.manifest)
  finally:outside.unlink(missing_ok=True)
 def test_rejects_ready_package_in_nested_updates_directory(self):
  nested=self.root/'nested';nested.mkdir();package=nested/'package.zip';package.write_bytes(b'payload');(self.root/'ready.json').write_text(json.dumps({'version':'2.0.11','package':str(package),'sha256':self.digest}),encoding='utf-8');self.assertRaises(RuntimeError,updater_engine.load_ready,self.manifest)
 def test_install_root_requires_full_installed_layout(self):
  install=self.root/'install';install.mkdir();self.assertIsNone(updater_engine.validate_install_root(install));(install/'FPV-Uhyliant-Update.exe').write_bytes(b'');(install/'FPV-Uhyliant-Launcher.exe').write_bytes(b'');(install/'app'/'current').mkdir(parents=True);(install/'app'/'current'/'FPV-Uhyliant.exe').write_bytes(b'');self.assertEqual(updater_engine.validate_install_root(install),install.resolve())
 def test_update_errors_hide_transport_and_filesystem_details(self):
  import urllib.error
  for action,message in (('check','Не вдалося перевірити оновлення'),('download','Не вдалося завантажити оновлення')):
   text=updater_engine.human_update_error(action,urllib.error.URLError('socket error at https://example.invalid'))
   self.assertIn(message,text);self.assertNotIn('socket error',text);self.assertNotIn('https://',text)
  self.assertIn('доступ до диска',updater_engine.human_update_error('download',OSError('C:\\\\private\\\\updates')))
if __name__=='__main__':unittest.main()
