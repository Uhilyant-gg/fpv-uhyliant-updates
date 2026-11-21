import json,tempfile,unittest
from pathlib import Path
from pairing import PairingRegistry,SecretStore,MetadataStore,JsonMetadataStore
class Store(SecretStore):
 available=True
 def __init__(self):self.data={}
 def put(self,key,value):self.data[key]=bytes(value)
 def delete(self,key):self.data.pop(key,None)
 def contains(self,key):return key in self.data
class Meta(MetadataStore):
 available=True
 def __init__(self):self.records=[];self.fail=False
 def load(self):return [dict(r) for r in self.records]
 def save(self,records):
  if self.fail:raise OSError('fail')
  self.records=[dict(r) for r in records]
class Clock:
 def __call__(self):return 100
class Tests(unittest.TestCase):
 def test_pairing_requires_both_stores(self):self.assertEqual(PairingRegistry(Store()).begin('Ground','peer'),{});self.assertEqual(PairingRegistry(metadata_store=Meta()).begin('Ground','peer'),{})
 def test_confirm_failure_preserves_pending_for_retry(self):
  s=Store();m=Meta();r=PairingRegistry(s,m);p=r.begin('Ground','peer');m.fail=True;self.assertFalse(r.confirm(p['id'],True));self.assertEqual(len(r.pending),1);self.assertEqual(s.data,{})
 def test_confirm_persists_metadata_without_secret_bytes(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');self.assertTrue(r.confirm(p['id'],True));self.assertNotIn('secret',m.records[0]);self.assertIn(m.records[0]['secretRef'],s.data)
 def test_reconcile_is_commit_after_persist(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);s.data.clear();m.fail=True;r.reconcile();self.assertEqual(len(r.trusted),1);m.fail=False;r.reconcile();self.assertEqual(r.trusted,[])
 def test_json_metadata_store_roundtrip_contains_no_secret(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'pairing.json';s=Store();meta=JsonMetadataStore(path);r=PairingRegistry(s,meta,Clock());p=r.begin('Ground','peer');self.assertTrue(r.confirm(p['id'],True));raw=path.read_text();self.assertNotIn(s.data[r.trusted[0]['secretRef']].hex(),raw);loaded=PairingRegistry(s,JsonMetadataStore(path));self.assertEqual(len(loaded.trusted),1)
 def test_json_metadata_store_rejects_unknown_envelope_fields(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'pairing.json';path.write_text(json.dumps({'schema':'fpv-uhyliant-pairing-metadata','version':1,'records':[],'secret':'x'}));r=PairingRegistry(Store(),JsonMetadataStore(path));self.assertFalse(r.metadataStoreAvailable);self.assertNotEqual(r.metadataError,'')
if __name__=='__main__':unittest.main()
