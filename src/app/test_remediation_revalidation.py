import unittest
from remediation_revalidation import remediation_revalidation
class Tests(unittest.TestCase):
 def test_failed_execution_problem(self):self.assertEqual(remediation_revalidation({}, {}, False)['health'],'problem')
 def test_missing_after_unknown(self):self.assertEqual(remediation_revalidation({'state':'problem'},None,True)['health'],'unknown')
 def test_ready_after_fix_revalidated(self):self.assertEqual(remediation_revalidation({'state':'problem'},{'state':'ready'},True)['health'],'ready')
 def test_no_change_is_attention(self):self.assertFalse(remediation_revalidation({'state':'problem'},{'state':'problem'},True)['changed'])
if __name__=='__main__':unittest.main()
