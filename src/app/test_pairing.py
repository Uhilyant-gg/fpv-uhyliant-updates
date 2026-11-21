import json,tempfile,unittest
from pathlib import Path
from pairing import PairingRegistry,SecretStore,MetadataStore,JsonMetadataStore
class Store(SecretStore):
 available=True
 def __init__(self):self.data={};self.fail=None
 def put(self,key,value):
  if self.fail=='put':raise OSError('put fail')
  self.data[key]=bytes(value)
 def get(self,key):
  if self.fail=='get':raise OSError('get fail')
  return self.data.get(key)
 def delete(self,key):
  if self.fail=='delete':raise OSError('delete fail')
  self.data.pop(key,None)
 def contains(self,key):
  if self.fail=='contains':raise OSError('contains fail')
  return key in self.data
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
 def test_pairing_requires_both_stores(self):
  self.assertEqual(PairingRegistry(secret_store=Store(),metadata_store=MetadataStore()).begin('Ground','peer'),{})
  self.assertEqual(PairingRegistry(secret_store=SecretStore(),metadata_store=Meta()).begin('Ground','peer'),{})
 def test_confirm_failure_preserves_pending_for_retry(self):
  s=Store();m=Meta();r=PairingRegistry(s,m);p=r.begin('Ground','peer');m.fail=True;self.assertFalse(r.confirm(p['id'],True));self.assertEqual(len(r.pending),1);self.assertEqual(s.data,{})
 def test_confirm_rollback_failure_blocks_new_pairing_until_reconcile(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');m.fail=True;s.fail='delete';self.assertFalse(r.confirm(p['id'],True));self.assertNotEqual(r.recoveryError,'');self.assertEqual(r.begin('Other','peer2'),{});s.fail=None;m.fail=False;r.reconcile();self.assertEqual(r.recoveryError,'')
 def test_confirm_persists_metadata_without_secret_bytes(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');self.assertTrue(r.confirm(p['id'],True));self.assertNotIn('secret',m.records[0]);self.assertIn(m.records[0]['secretRef'],s.data)
 def test_revoke_rolls_secret_back_when_metadata_write_fails(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);key=r.trusted[0]['secretRef'];original=s.data[key];m.fail=True;self.assertFalse(r.revoke(p['id']));self.assertEqual(s.data[key],original);self.assertEqual(len(r.trusted),1)
 def test_revoke_rollback_failure_is_explicit_and_blocks_mutation(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);m.fail=True
  original_save=m.save
  def fail_save(records):s.fail='put';original_save(records)
  m.save=fail_save;self.assertFalse(r.revoke(p['id']));self.assertNotEqual(r.recoveryError,'');self.assertEqual(len(r.trusted),1);self.assertFalse(r.revoke(p['id']))
 def test_revoke_missing_secret_requires_reconcile(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);s.data.clear();self.assertFalse(r.revoke(p['id']));self.assertNotEqual(r.recoveryError,'');r.reconcile();self.assertEqual(r.trusted,[]);self.assertEqual(r.recoveryError,'')
 def test_revoke_removes_secret_and_metadata(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);self.assertTrue(r.revoke(p['id']));self.assertEqual(s.data,{});self.assertEqual(m.records,[]);self.assertEqual(r.trusted,[])
 def test_secret_failure_is_reported_without_fabricating_absence(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);s.fail='contains';r.reconcile();self.assertEqual(len(r.trusted),1);self.assertIn('contains fail',r.secretStoreError)
 def test_reconcile_is_commit_after_persist_and_retries_after_transient_error(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);s.data.clear();m.fail=True;r.reconcile();self.assertEqual(len(r.trusted),1);self.assertNotEqual(r.metadataError,'');m.fail=False;r.reconcile();self.assertEqual(r.trusted,[]);self.assertEqual(r.metadataError,'')
 def test_json_metadata_store_roundtrip_contains_no_secret(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'pairing.json';s=Store();r=PairingRegistry(s,JsonMetadataStore(path),Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);self.assertNotIn(s.data[r.trusted[0]['secretRef']].hex(),path.read_text());self.assertEqual(len(PairingRegistry(s,JsonMetadataStore(path)).trusted),1)
 def test_json_metadata_store_rejects_unknown_envelope_fields(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'pairing.json';path.write_text(json.dumps({'schema':'fpv-uhyliant-pairing-metadata','version':1,'records':[],'secret':'x'}));r=PairingRegistry(Store(),JsonMetadataStore(path));self.assertNotEqual(r.metadataError,'');self.assertEqual(r.begin('Ground','peer'),{})
 def test_duplicate_record_ids_are_rejected(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);m.records.append(dict(m.records[0]));loaded=PairingRegistry(s,m);self.assertNotEqual(loaded.metadataError,'');self.assertEqual(loaded.trusted,[])
if __name__=='__main__':unittest.main()
