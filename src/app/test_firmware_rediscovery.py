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
 def test_unrecognized_majestic_text_is_not_fresh_probe_evidence(self):
  r=FirmwareRediscovery(lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['Majestic cached identity']},lambda _:None).wait('192.168.1.50',1,0);self.assertFalse(r['rediscovered']);self.assertFalse(r['identity']['verified'])
 def test_status_endpoint_is_recognized_as_fresh_probe_evidence(self):
  r=FirmwareRediscovery(lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']},lambda _:None).wait('192.168.1.50',1,0);self.assertTrue(r['rediscovered']);self.assertTrue(r['identity']['verified'])
 def test_probe_exception_is_bounded_failure(self):
  calls=[]
  def probe(host):calls.append(host);raise RuntimeError('probe failed')
  r=FirmwareRediscovery(probe,lambda _:None).wait('192.168.1.50',2,0);self.assertFalse(r['rediscovered']);self.assertEqual(r['attempts'],2);self.assertEqual(len(calls),2)
if __name__=='__main__':unittest.main()
