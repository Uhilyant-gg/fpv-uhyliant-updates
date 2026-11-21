import unittest
from firmware_rediscovery import FirmwareRediscovery
IDENTITY={'platform':'ssc30kq','sensor':'imx335'}
class Tests(unittest.TestCase):
 def test_waits_until_verified_openipc_returns(self):
  values=[{}, {'openipc':True,'identity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['Majestic /api/v1/config.json']}]
  r=FirmwareRediscovery(lambda host:values.pop(0),lambda _:None).wait('192.168.1.50',3,0);self.assertTrue(r['rediscovered']);self.assertEqual(r['attempts'],2);self.assertEqual(r['identity']['firmware'],'new')
 def test_dhcp_change_accepts_only_matching_hardware_identity(self):
  calls=[]
  def probe(host):
   calls.append(host)
   if host=='192.168.1.60':return {'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx415','firmware':'other'},'evidence':['OpenIPC status.cgi']}
   if host=='192.168.1.70':return {'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']}
   return {}
  r=FirmwareRediscovery(probe,lambda _:None,lambda old:['192.168.1.60','192.168.1.70']).wait('192.168.1.50',1,0,IDENTITY);self.assertTrue(r['rediscovered']);self.assertEqual(r['host'],'192.168.1.70');self.assertIn('192.168.1.60',calls)
 def test_dhcp_candidate_requires_complete_expected_identity(self):
  result={'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']}
  r=FirmwareRediscovery(lambda host:result,lambda _:None,lambda old:['192.168.1.70']).wait('192.168.1.50',1,0,{'platform':'ssc30kq'});self.assertTrue(r['rediscovered']);self.assertEqual(r['host'],'192.168.1.50')
 def test_generic_reachable_result_never_completes(self):
  r=FirmwareRediscovery(lambda host:{'openipc':False,'identity':{}},lambda _:None).wait('192.168.1.50',2,0);self.assertFalse(r['rediscovered'])
 def test_caller_verified_flag_without_fresh_evidence_never_completes(self):
  r=FirmwareRediscovery(lambda host:{'openipc':True,'identity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':[]},lambda _:None).wait('192.168.1.50',1,0);self.assertFalse(r['rediscovered'])
 def test_probe_exception_is_bounded_failure(self):
  calls=[]
  def probe(host):calls.append(host);raise RuntimeError('probe failed')
  r=FirmwareRediscovery(probe,lambda _:None).wait('192.168.1.50',2,0);self.assertFalse(r['rediscovered']);self.assertEqual(r['attempts'],2);self.assertEqual(len(calls),2)
if __name__=='__main__':unittest.main()
