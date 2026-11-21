import unittest
from hardware_e2e import hardware_e2e_readiness
class Tests(unittest.TestCase):
 def device(self):return {'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}
 def evidence(self):return {'summary':{'safeRoutes':1},'devices':[{'host':'192.168.1.50','reachable':True,'openipcVerified':True}]}
 def firmware(self):return {'artifact':{'verified':True,'sha256':'a'*64,'size':1024,'build':'2026.11.21'},'plan':{'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':'token','artifactSha256':'a'*64,'artifactSize':1024},'approval':{'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':'token','artifactSha256':'a'*64}}
 def test_complete_physical_prerequisites_are_ready(self):
  r=hardware_e2e_readiness(self.device(),self.evidence(),True,True,self.firmware());self.assertTrue(r['ready']);self.assertEqual(r['missing'],[]);self.assertEqual(r['artifact']['sha256'],'a'*64);self.assertEqual(r['approvalToken'],'token')
 def test_credentials_and_host_key_are_explicit_gates(self):
  r=hardware_e2e_readiness(self.device(),self.evidence(),False,False,self.firmware());self.assertIn('credentialsPresent',r['missing']);self.assertIn('hostKeyAccepted',r['missing'])
 def test_generic_reachability_cannot_replace_openipc_identity(self):
  d=self.device();d['openipcIdentity']={'verified':False};r=hardware_e2e_readiness(d,self.evidence(),True,True,self.firmware());self.assertIn('openipcVerified',r['missing']);self.assertIn('hardwareIdentityObserved',r['missing'])
 def test_unknown_reachability_fails_closed(self):
  e=self.evidence();e['devices'][0]['reachable']=None;r=hardware_e2e_readiness(self.device(),e,True,True,self.firmware());self.assertIn('deviceReachableObserved',r['missing'])
 def test_artifact_requires_real_sha_and_positive_integer_size(self):
  for sha,size in (('short',1024),('a'*64,0),('a'*64,1.5)):
   fw=self.firmware();fw['artifact']['sha256']=sha;fw['artifact']['size']=size;r=hardware_e2e_readiness(self.device(),self.evidence(),True,True,fw);self.assertIn('firmwareArtifactVerified',r['missing'])
 def test_plan_approval_and_artifact_must_form_one_immutable_binding(self):
  for section,key,value in (('plan','deviceId','other'),('approval','deviceId','other'),('plan','approvalToken','other'),('approval','approvalToken','other'),('plan','artifactSha256','b'*64),('approval','artifactSha256','b'*64),('plan','artifactSize',2048),('plan','mode','primary')):
   fw=self.firmware();fw[section][key]=value;r=hardware_e2e_readiness(self.device(),self.evidence(),True,True,fw);self.assertIn('executionPlanReady',r['missing'])
if __name__=='__main__':unittest.main()
