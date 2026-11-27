import unittest
from pairing import SecretStoreUnavailable
from windows_secret_store import WindowsCredentialSecretStore
class Api:
 def __init__(self):self.data={};self.fail=None
 def put(self,key,value):
  if self.fail=='put':raise OSError('put failed')
  self.data[key]=bytes(value)
 def get(self,key):
  if self.fail=='get':raise OSError('get failed')
  return self.data.get(key)
 def delete(self,key):
  if self.fail=='delete':raise OSError('delete failed')
  self.data.pop(key,None)
class Tests(unittest.TestCase):
 def test_non_windows_is_safely_unavailable(self):
  s=WindowsCredentialSecretStore(platform='linux');self.assertFalse(s.available);self.assertFalse(s.validation_pending)
 def test_adapter_roundtrip_and_namespaces_target(self):
  a=Api();s=WindowsCredentialSecretStore(api=a,platform='win32');s.put('pairing/abc',b'secret');self.assertTrue(s.contains('pairing/abc'));self.assertEqual(s.get('pairing/abc'),b'secret');self.assertIn('FPV-Uhyliant/pairing/abc',a.data);s.delete('pairing/abc');self.assertFalse(s.contains('pairing/abc'))
 def test_invalid_key_and_empty_secret_are_rejected(self):
  s=WindowsCredentialSecretStore(api=Api(),platform='win32')
  with self.assertRaises(SecretStoreUnavailable):s.put('other/abc',b'secret')
  with self.assertRaises(SecretStoreUnavailable):s.put('pairing/abc',b'')
 def test_api_failure_does_not_turn_into_false_absence(self):
  a=Api();a.fail='get';s=WindowsCredentialSecretStore(api=a,platform='win32')
  with self.assertRaises(OSError):s.contains('pairing/abc')
 def test_backup_key_uses_distinct_namespace(self):
  a=Api();s=WindowsCredentialSecretStore(api=a,platform='win32');s.put('backup/abc',b'key');self.assertEqual(s.get('backup/abc'),b'key');self.assertIn('FPV-Uhyliant/backup/abc',a.data)
if __name__=='__main__':unittest.main()
