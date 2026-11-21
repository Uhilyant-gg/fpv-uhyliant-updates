import tempfile,unittest
from pathlib import Path
from release_policy import sha256_file,validate_release_inputs,verify_sha256
class Tests(unittest.TestCase):
 def test_release_channels_and_prerelease_policy(self):
  self.assertTrue(validate_release_inputs('2.0.10','test',True));self.assertTrue(validate_release_inputs('2.0.10','stable',False))
  with self.assertRaises(ValueError):validate_release_inputs('2.0','stable',False)
  with self.assertRaises(ValueError):validate_release_inputs('2.0.10','other',True)
  with self.assertRaises(ValueError):validate_release_inputs('2.0.10','development',False)
 def test_artifact_digest_verification(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'artifact';p.write_bytes(b'known artifact');digest=sha256_file(p);self.assertTrue(verify_sha256(p,digest));p.write_bytes(b'changed');self.assertFalse(verify_sha256(p,digest));self.assertFalse(verify_sha256(p,'bad'))
if __name__=='__main__':unittest.main()
