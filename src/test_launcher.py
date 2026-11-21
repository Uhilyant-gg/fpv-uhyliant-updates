import unittest
from launcher import valid_pending
class Tests(unittest.TestCase):
 def test_pending_state_requires_version_and_package_digest(self):
  self.assertTrue(valid_pending({'current':'2.0.11','packageSha256':'a'*64}));self.assertFalse(valid_pending({'current':'2.0.11'}));self.assertFalse(valid_pending({'current':'','packageSha256':'a'*64}));self.assertFalse(valid_pending({'current':'2.0.11','packageSha256':'bad'}))
if __name__=='__main__':unittest.main()
