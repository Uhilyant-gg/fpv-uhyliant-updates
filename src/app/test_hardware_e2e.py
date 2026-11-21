import unittest
from hardware_e2e import hardware_e2e_readiness
class Tests(unittest.TestCase):
 def device(self):return {'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}
 def evidence(self):return {'summary':{'safeRoutes':1},'devices':[{'host':'192.168.1.50','reachable':True,'openipcVerified':True}]}
 def firmware(self):return {'artifact':{'verified':True,'sha256':'a'*64,'size':1024,'build':'2026.11.21'},'plan':{'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade'}}
 def test_complete_physical_prerequisites_are_ready(self):
  r=hardware_e2e_readiness(self.device(),self.evidence(),True,True,self.firmware());self.assertTrue(r['ready']);self.assertEqual(r['missing'],[]);self.assertEqual(r['artifact']['sha256'],'a'*64);self.assertEqual(r['profile'],'ssc30kq-imx335')
 def test_credentials_and_host_key_are_explicit_gates(self):
  r=hardware_e2e_readiness(self.device(),self.evidence(),False,False,self.firmware());self.assertFalse(r['ready']);self.assertIn('credentialsPresent',r['missing']);self.assertIn('hostKeyAccepted',r['missing'])
 def test_generic_reachability_cannot_replace_openipc_identity(self):
  d=self.device();d['openipcIdentity']={'verified':False};r=hardware_e2e_readiness(d,self.evidence(),True,True,self.firmware());self.assertFalse(r['ready']);self.assertIn('openipcVerified',r['missing']);self.assertIn('hardwareIdentityObserved',r['missing'])
 def test_unknown_reachability_fails_closed(self):
  e=self.evidence();e['devices'][0]['reachable']=None;r=hardware_e2e_readiness(self.device(),e,True,True,self.firmware());self.assertFalse(r['ready']);self.assertIn('deviceReachableObserved',r['missing'])
 def test_artifact_and_execution_plan_are_required(self):
  r=hardware_e2e_readiness(self.device(),self.evidence(),True,True,{});self.assertFalse(r['ready']);self.assertIn('firmwareArtifactVerified',r['missing']);self.assertIn('executionPlanReady',r['missing'])
 def test_plan_must_be_bound_to_selected_device(self):
  fw=self.firmware();fw['plan']['deviceId']='other';r=hardware_e2e_readiness(self.device(),self.evidence(),True,True,fw);self.assertFalse(r['ready']);self.assertIn('executionPlanReady',r['missing'])
if __name__=='__main__':unittest.main()
