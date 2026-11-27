import hashlib,tempfile,unittest,zipfile
from pathlib import Path
from update_package import extract_verified_zip
class Tests(unittest.TestCase):
 def make_zip(self,root,entries):
  p=root/'p.zip'
  with zipfile.ZipFile(p,'w') as z:
   for name,data in entries:
    info=zipfile.ZipInfo(name);info.filename=name;z.writestr(info,data)
  return p
 def digest(self,p):return hashlib.sha256(p.read_bytes()).hexdigest()
 def test_verified_zip_extracts(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);p=self.make_zip(r,[('FPV-Uhyliant.exe',b'x'),('dir/a.txt',b'a')]);self.assertTrue(extract_verified_zip(p,r/'out',self.digest(p)));self.assertEqual((r/'out/dir/a.txt').read_bytes(),b'a')
 def test_digest_mismatch_rejected_before_extraction(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);p=self.make_zip(r,[('x',b'x')]);self.assertRaises(ValueError,extract_verified_zip,p,r/'out','0'*64);self.assertFalse((r/'out').exists())
 def test_traversal_and_windows_backslash_paths_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   for name in ('../escape','dir\\evil'):
    p=self.make_zip(r,[(name,b'x')]);self.assertRaises(ValueError,extract_verified_zip,p,r/'out',self.digest(p))
 def test_casefold_duplicate_path_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);p=self.make_zip(r,[('A.txt',b'a'),('a.txt',b'b')]);self.assertRaises(ValueError,extract_verified_zip,p,r/'out',self.digest(p))
if __name__=='__main__':unittest.main()
