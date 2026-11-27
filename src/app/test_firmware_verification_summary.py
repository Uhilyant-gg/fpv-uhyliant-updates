import unittest
from firmware_verification_summary import firmware_verification_summary
class Tests(unittest.TestCase):
 def test_missing_is_unknown(self):self.assertEqual(firmware_verification_summary(None)['health'],'unknown')
 def test_pending_is_not_success(self):self.assertEqual(firmware_verification_summary({'state':'reboot-pending'})['health'],'attention')
 def test_verified_requires_observed_firmware(self):self.assertEqual(firmware_verification_summary({'state':'verified','verification':{'ok':True}})['health'],'unknown')
 def test_verified_with_observed_firmware_ready(self):self.assertEqual(firmware_verification_summary({'state':'verified','verification':{'ok':True,'observedFirmware':'v2'}})['health'],'ready')
 def test_error_is_problem(self):self.assertEqual(firmware_verification_summary({'state':'error'})['health'],'problem')
if __name__=='__main__':unittest.main()
