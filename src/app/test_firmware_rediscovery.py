import unittest
from firmware_rediscovery import FirmwareRediscovery
class Tests(unittest.TestCase):
 def test_waits_until_verified_openipc_returns(self):
  values=[{}, {'openipc':True,'identity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['Majestic /api/v1/config.json']}]
  r=FirmwareRediscovery(lambda host:values.pop(0),lambda _:None).wait('192.168.1.50',3,0);self.assertTrue(r['rediscovered']);self.assertEqual(r['attempts'],2);self.assertEqual(r['identity']['firmware'],'new')
 def test_generic_reachable_result_never_completes(self):
  r=FirmwareRediscovery(lambda host:{'openipc':False,'identity':{}},lambda _:None).wait('192.168.1.50',2,0);self.assertFalse(r['rediscovered']);self.assertFalse(r['identity']['verified'])
 def test_caller_verified_flag_without_fresh_evidence_never_completes(self):
  r=FirmwareRediscovery(lambda host:{'openipc':True,'identity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':[]},lambda _:None).wait('192.168.1.50',1,0);self.assertFalse(r['rediscovered']);self.assertFalse(r['identity']['verified'])
if __name__=='__main__':unittest.main()
