import unittest
from openipc_upgrade_transport import OpenIPCUpgradeAdapter
SHA='a'*64
ARTIFACT={'verified':True,'sha256':SHA,'size':123}
PLAN={'ready':True,'approvalToken':'approved','artifactSha256':SHA,'artifactSize':123}
APPROVAL={'ready':True,'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','artifactSha256':SHA,'approvalToken':'approved'}
def handoff():return {'deviceId':'cam','profile':'ssc30kq-imx335','mode':'upgrade','host':'192.168.1.50','platform':'ssc30kq','sensor':'imx335','verifiedOpenIPC':True,'artifact':dict(ARTIFACT),'plan':dict(PLAN),'approval':dict(APPROVAL)}
class Devices:
 def __init__(self,verified=True):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':verified,'platform':'ssc30kq','sensor':'imx335'}}]
class Transport:
 def __init__(self,auth=True,result=True):self.calls=[];self.auth=auth;self.result=result
 def authenticate(self,host):self.calls.append(('auth',host));return self.auth
 def run(self,host,argv):self.calls.append(('run',host,argv));return self.result
class Tests(unittest.TestCase):
 def test_authentication_precedes_fixed_upgrade(self):
  t=Transport();a=OpenIPCUpgradeAdapter(Devices(),t);self.assertTrue(a.execute('cam','ssc30kq-imx335','upgrade',dict(ARTIFACT),dict(PLAN),handoff()));self.assertEqual(t.calls,[('auth','192.168.1.50'),('run','192.168.1.50',['sysupgrade','-k','-r'])])
 def test_auth_failure_blocks_destructive_execute(self):
  t=Transport(False);self.assertFalse(OpenIPCUpgradeAdapter(Devices(),t).execute('cam','ssc30kq-imx335','upgrade',dict(ARTIFACT),dict(PLAN),handoff()));self.assertEqual(t.calls,[('auth','192.168.1.50')])
 def test_unverified_camera_never_authenticates_or_runs(self):
  t=Transport();self.assertFalse(OpenIPCUpgradeAdapter(Devices(False),t).execute('cam','ssc30kq-imx335','upgrade',dict(ARTIFACT),dict(PLAN),handoff()));self.assertEqual(t.calls,[])
 def test_identity_change_after_auth_blocks_run(self):
  d=Devices();t=Transport();original=t.authenticate
  def auth(host):ok=original(host);d.items[0]['openipcIdentity']['sensor']='other';return ok
  t.authenticate=auth;self.assertFalse(OpenIPCUpgradeAdapter(d,t).execute('cam','ssc30kq-imx335','upgrade',dict(ARTIFACT),dict(PLAN),handoff()));self.assertEqual(len([c for c in t.calls if c[0]=='run']),0)
 def test_missing_or_mismatched_handoff_never_authenticates(self):
  cases=[({},dict(PLAN),handoff()),(dict(ARTIFACT),{},handoff()),(dict(ARTIFACT),dict(PLAN),None),(dict(ARTIFACT),{**PLAN,'artifactSha256':'b'*64},handoff()),(dict(ARTIFACT),{**PLAN,'artifactSize':124},handoff()),({**ARTIFACT,'verified':False},dict(PLAN),handoff()),({**ARTIFACT,'size':0},dict(PLAN),handoff())]
  for artifact,plan,h in cases:
   with self.subTest(artifact=artifact,plan=plan,handoff=h):
    t=Transport();self.assertFalse(OpenIPCUpgradeAdapter(Devices(),t).execute('cam','ssc30kq-imx335','upgrade',artifact,plan,h));self.assertEqual(t.calls,[])
 def test_handoff_identity_or_approval_mutation_blocks_before_authentication(self):
  for key,value in (('deviceId','other'),('profile','other'),('mode','primary'),('host','192.168.1.99'),('platform','other'),('sensor','other'),('verifiedOpenIPC',False)):
   h=handoff();h[key]=value;t=Transport();self.assertFalse(OpenIPCUpgradeAdapter(Devices(),t).execute('cam','ssc30kq-imx335','upgrade',dict(ARTIFACT),dict(PLAN),h));self.assertEqual(t.calls,[])
  for key,value in (('approvalToken','mutated'),('ready',False)):
   h=handoff();h['approval'][key]=value;t=Transport();self.assertFalse(OpenIPCUpgradeAdapter(Devices(),t).execute('cam','ssc30kq-imx335','upgrade',dict(ARTIFACT),dict(PLAN),h));self.assertEqual(t.calls,[])
 def test_live_host_change_after_auth_is_rejected(self):
  d=Devices();t=Transport();original=t.authenticate
  def auth(host):ok=original(host);d.items[0]['host']='192.168.1.99';return ok
  t.authenticate=auth;self.assertFalse(OpenIPCUpgradeAdapter(d,t).execute('cam','ssc30kq-imx335','upgrade',dict(ARTIFACT),dict(PLAN),handoff()));self.assertEqual(len([c for c in t.calls if c[0]=='run']),0)
if __name__=='__main__':unittest.main()
