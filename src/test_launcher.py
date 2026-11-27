import unittest
from launcher import valid_pending
class Tests(unittest.TestCase):
 def pending(self):return {'current':'2.0.12','pendingStartup':True,'packageSha256':'a'*64,'updatedAt':1}
 def test_pending_state_requires_complete_exact_schema(self):
  state=self.pending();self.assertTrue(valid_pending(state))
  for key in tuple(state):
   bad=self.pending();bad.pop(key);self.assertFalse(valid_pending(bad))
  bad=self.pending();bad['extra']=True;self.assertFalse(valid_pending(bad))
 def test_pending_state_requires_true_pending_flag_version_digest_and_timestamp(self):
  bad=self.pending();bad['pendingStartup']=False;self.assertFalse(valid_pending(bad));bad=self.pending();bad['current']='';self.assertFalse(valid_pending(bad));bad=self.pending();bad['packageSha256']='bad';self.assertFalse(valid_pending(bad));bad=self.pending();bad['updatedAt']=0;self.assertFalse(valid_pending(bad));bad=self.pending();bad['updatedAt']='1';self.assertFalse(valid_pending(bad))
if __name__=='__main__':unittest.main()
