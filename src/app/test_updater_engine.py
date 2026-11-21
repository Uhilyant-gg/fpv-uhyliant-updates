import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import updater_engine


class UpdaterReadyStateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.original=updater_engine.UP;updater_engine.UP=self.root
        self.payload=self.root/'package.zip';self.payload.write_bytes(b'payload')
        self.digest=hashlib.sha256(b'payload').hexdigest()
        self.manifest={'version':'2.0.11','package':{'file':'package.zip','sha256':self.digest}}
        (self.root/'ready.json').write_text(json.dumps({'version':'2.0.11','package':str(self.payload)}),encoding='utf-8')
    def tearDown(self):
        updater_engine.UP=self.original;self.temp.cleanup()
    def test_ready_state_matches_verified_manifest(self):
        ready=updater_engine.load_ready(self.manifest);self.assertEqual(ready['version'],'2.0.11')
    def test_rejects_changed_package_after_download(self):
        self.payload.write_bytes(b'tampered')
        with self.assertRaises(RuntimeError):updater_engine.load_ready(self.manifest)
    def test_rejects_manifest_version_mismatch(self):
        bad=dict(self.manifest);bad['version']='2.0.12'
        with self.assertRaises(RuntimeError):updater_engine.load_ready(bad)


if __name__=='__main__':unittest.main()
