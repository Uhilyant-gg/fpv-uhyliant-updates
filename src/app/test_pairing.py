import unittest
from pairing import PairingRegistry,SecretStore
class Store(SecretStore):
 available=True
 def __init__(self):self.data={}
 def put(self,key,value):self.data[key]=bytes(value)
 def delete(self,key):self.data.pop(key)
class Clock:
 def __call__(self):return 100
class Tests(unittest.TestCase):
 def test_pairing_is_blocked_without_protected_store(self):self.assertEqual(PairingRegistry().begin('Ground','10.0.0.1'),{})
 def test_confirm_requires_explicit_approval_and_keeps_secret_out_of_public_state(self):
  s=Store();r=PairingRegistry(s,Clock());p=r.begin('Ground','10.0.0.1');self.assertNotIn('secret',p);self.assertFalse(r.confirm(p['id'],False));self.assertEqual(r.trusted,[]);p=r.begin('Ground','10.0.0.1');self.assertTrue(r.confirm(p['id'],True));self.assertEqual(r.trusted[0]['state'],'trusted');self.assertNotIn('secret',r.trusted[0]);self.assertIn(r.trusted[0]['secretRef'],s.data)
 def test_revoke_deletes_secret_before_trust_record(self):
  s=Store();r=PairingRegistry(s,Clock());p=r.begin('Ground','peer');r.confirm(p['id'],True);key=r.trusted[0]['secretRef'];self.assertTrue(r.revoke(p['id']));self.assertNotIn(key,s.data);self.assertEqual(r.trusted,[])
 def test_cancel_drops_pending_without_storing_secret(self):
  s=Store();r=PairingRegistry(s);p=r.begin('Ground','peer');self.assertTrue(r.cancel(p['id']));self.assertEqual(r.pending,[]);self.assertEqual(s.data,{})
if __name__=='__main__':unittest.main()
