import threading,time,unittest
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
 def test_dhcp_candidates_are_probed_with_bounded_parallel_fanout(self):
  active=[0];peak=[0];lock=threading.Lock()
  def probe(host):
   with lock:active[0]+=1;peak[0]=max(peak[0],active[0])
   time.sleep(.01)
   with lock:active[0]-=1
   return {}
  hosts=['192.168.1.%d'%n for n in range(1,80)]
  r=FirmwareRediscovery(probe,lambda _:None,lambda old:hosts).wait('192.168.1.250',1,0,IDENTITY);self.assertFalse(r['rediscovered']);self.assertGreater(peak[0],1);self.assertLessEqual(peak[0],24)
 def test_matching_candidate_returns_without_waiting_for_other_running_probes(self):
  gate=threading.Event();started=threading.Event();match={'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']}
  def probe(host):
   if host=='192.168.1.50':return {}
   if host=='192.168.1.70':return match
   started.set();gate.wait(2);return {}
  hosts=['192.168.1.60','192.168.1.70']+['192.168.1.%d'%n for n in range(71,95)]
  try:
   before=time.monotonic();r=FirmwareRediscovery(probe,lambda _:None,lambda old:hosts).wait('192.168.1.50',1,0,IDENTITY);elapsed=time.monotonic()-before
   self.assertTrue(started.is_set());self.assertTrue(r['rediscovered']);self.assertEqual(r['host'],'192.168.1.70');self.assertLess(elapsed,1.0)
  finally:gate.set()
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
