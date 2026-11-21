import unittest
from pairing import PairingRegistry,SecretStore,MetadataStore
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
 def test_confirm_persists_metadata_without_secret_bytes(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');self.assertTrue(r.confirm(p['id'],True));self.assertNotIn('secret',m.records[0]);self.assertIn(m.records[0]['secretRef'],s.data)
 def test_metadata_failure_removes_new_secret_and_does_not_trust(self):
  s=Store();m=Meta();r=PairingRegistry(s,m);p=r.begin('Ground','peer');m.fail=True;self.assertFalse(r.confirm(p['id'],True));self.assertEqual(s.data,{});self.assertEqual(r.trusted,[])
 def test_reloads_trust_metadata_and_reconciles_missing_secret(self):
  s=Store();m=Meta();r=PairingRegistry(s,m,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);self.assertEqual(len(PairingRegistry(s,m).trusted),1);s.data.clear();r2=PairingRegistry(s,m);r2.reconcile();self.assertEqual(r2.trusted,[])
 def test_revoke_deletes_secret_and_persists_empty_trust(self):
  s=Store();m=Meta();r=PairingRegistry(s,m);p=r.begin('Ground','peer');r.confirm(p['id'],True);self.assertTrue(r.revoke(p['id']));self.assertEqual(s.data,{});self.assertEqual(m.records,[])
 def test_cancel_drops_pending_without_storing_secret(self):
  s=Store();m=Meta();r=PairingRegistry(s,m);p=r.begin('Ground','peer');self.assertTrue(r.cancel(p['id']));self.assertEqual(r.pending,[]);self.assertEqual(s.data,{})
if __name__=='__main__':unittest.main()
