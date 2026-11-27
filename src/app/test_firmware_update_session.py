import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
from firmware_update_session import FirmwareUpdateSession
class Devices:
 def __init__(self):self.items=[{'id':'cam','active':False,'host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}},{'id':'other','active':True,'host':'192.168.1.51','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx415','firmware':'old','evidence':['OpenIPC status.cgi']}}]
class Transport:
 def __init__(self,auth=True):self.auth=auth;self.calls=[]
 def authenticate(self,host):self.calls.append(('auth',host));return self.auth
 def run(self,host,argv):self.calls.append(('run',host,list(argv)));return True
class Credentials:
 def __init__(self,username='root',password='pw'):self.username=username;self.password=password
 def secret(self):return self.password
 def snapshot(self):return {'username':self.username,'hasPassword':bool(self.password)}
class Preflight:
 def __init__(self,center,**changes):
  i={'ready':True,'deviceId':'cam','host':'192.168.1.50','platform':'ssc30kq','sensor':'imx335','profile':'ssc30kq-imx335','mode':'upgrade','approvalToken':center.result['approvalToken']};i.update(changes);self.readiness=i
class SessionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();image=Path(self.tmp.name)/'fw.bin';image.write_bytes(b'x');self.devices=Devices();self.center=FirmwareCenter(self.devices);self.center.verifyImage(str(image),hashlib.sha256(b'x').hexdigest());self.center.precheck('cam','ssc30kq-imx335','upgrade',False,False);self.center.prepareExecution('cam','ssc30kq-imx335','upgrade');self.executor=FirmwareExecutor(self.center);self.session=FirmwareUpdateSession(self.executor,self.devices,probe=lambda host:{},candidates=lambda host:[],sleep=lambda _:None,rediscovery_attempts=1,rediscovery_interval=0)
 def tearDown(self):self.tmp.cleanup()
 def authenticate(self,preflight=None):
  with patch('firmware_update_session.AuthenticatedCameraTransport') as factory:
   transport=Transport();factory.return_value=transport;ok=self.session.enableAuthenticatedTransport(Credentials(),preflight or Preflight(self.center));return ok,transport
 def test_preflight_targets_device_id_not_unrelated_active_device(self):ok,_=self.authenticate();self.assertTrue(ok);self.assertTrue(self.session.result['enabled'])
 def test_preflight_requires_complete_approved_transaction_identity(self):
  for change in ({'deviceId':''},{'profile':''},{'mode':'primary'},{'approvalToken':''},{'host':'192.168.1.51'},{'sensor':'imx415'}):self.session.disableTransport();ok,_=self.authenticate(Preflight(self.center,**change));self.assertFalse(ok)
 def test_authentication_rejects_stale_plan_or_approval(self):
  preflight=Preflight(self.center);self.center._plan['approvalToken']='changed';ok,_=self.authenticate(preflight);self.assertFalse(ok)
 def test_authenticated_binding_must_still_match_at_execute(self):ok,_=self.authenticate();self.assertTrue(ok);self.center._plan['approvalToken']='changed';self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.session.result['state'],'blocked')
 def test_successful_bound_session_still_runs_fixed_upgrade(self):ok,transport=self.authenticate();self.assertTrue(ok);self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(transport.calls,[('auth','192.168.1.50'),('run','192.168.1.50',['sysupgrade','-k','-r'])])
 def test_credentials_never_enter_session_result_or_binding(self):ok,_=self.authenticate();self.assertTrue(ok);text=(repr(self.session.result)+repr(self.session._preflight_binding)).lower();self.assertNotIn('password',text);self.assertNotIn("'pw'",text)
if __name__=='__main__':unittest.main()
