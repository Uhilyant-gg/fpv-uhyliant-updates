"""Windows-only integration coverage for real Credential Manager pairing storage."""
import secrets
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from pairing import JsonMetadataStore,PairingRegistry
from windows_secret_store import WindowsCredentialSecretStore
@unittest.skipUnless(sys.platform=='win32','requires Windows Credential Manager')
class WindowsCredentialManagerIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.store=WindowsCredentialSecretStore();self.assertTrue(self.store.available,self.store.error);self.key='pairing/ci-'+uuid.uuid4().hex
 def tearDown(self):
  if getattr(self,'store',None) and self.store.available:
   try:self.store.delete(self.key)
   except Exception:pass
 def test_real_windows_roundtrip_overwrite_and_delete(self):
  first=secrets.token_bytes(32);self.store.put(self.key,first);self.assertTrue(self.store.contains(self.key));self.assertEqual(self.store.get(self.key),first);replacement=secrets.token_bytes(32);self.store.put(self.key,replacement);self.assertEqual(self.store.get(self.key),replacement);self.store.delete(self.key);self.assertFalse(self.store.contains(self.key));self.assertIsNone(self.store.get(self.key))
 def test_registry_persists_recovers_and_revokes_with_real_store(self):
  with tempfile.TemporaryDirectory() as temp:
   metadata=JsonMetadataStore(Path(temp)/'pairing-trust.json');registry=PairingRegistry(self.store,metadata);pending=registry.begin('CI peer','local-integration-test');self.assertTrue(pending);self.key='pairing/'+pending['id'];self.assertTrue(registry.confirm(pending['id'],True));self.assertTrue(self.store.contains(self.key));self.assertEqual(len(registry.trusted),1);restarted=PairingRegistry(self.store,metadata);restarted.reconcile();self.assertEqual(len(restarted.trusted),1);self.assertEqual(restarted.trusted[0]['id'],pending['id']);self.assertTrue(restarted.revoke(pending['id']));self.assertFalse(self.store.contains(self.key));final=PairingRegistry(self.store,metadata);final.reconcile();self.assertEqual(final.trusted,[])
if __name__=='__main__':unittest.main()
