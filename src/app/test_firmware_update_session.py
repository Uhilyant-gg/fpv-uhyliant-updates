import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
from firmware_update_session import FirmwareUpdateSession
class Devices:
 def __init__(self):self.items=[{'id':'cam','active':True,'host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]
class Transport:
 def __init__(self,auth=True):self.auth=auth;self.calls=[]
 def authenticate(self,host):self.calls.append(('auth',host));return self.auth
 def run(self,host,argv):self.calls.append(('run',host,list(argv)));return True
class Credentials:
 def __init__(self,username='root',password='pw'):self.username=username;self.password=password
 def secret(self):return self.password
 def snapshot(self):return {'username':self.username,'hasPassword':bool(self.password)}
class Preflight:
 def __init__(self,ready=True,host='192.168.1.50',platform='ssc30kq',sensor='imx335'):self.readiness={'ready':bool(ready),'host':host,'platform':platform,'sensor':sensor}
class SessionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();image=Path(self.tmp.name)/'fw.bin';image.write_bytes(b'x');self.devices=Devices();center=FirmwareCenter(self.devices);center.verifyImage(str(image),hashlib.sha256(b'x').hexdigest());center.precheck('cam','ssc30kq-imx335','upgrade',True,True);center.prepareExecution('cam','ssc30kq-imx335','upgrade');self.executor=FirmwareExecutor(center);self.probe_calls=[];self.candidate_calls=[]
  def probe(host):self.probe_calls.append(host);return {}
  def candidates(host):self.candidate_calls.append(host);return []
  self.session=FirmwareUpdateSession(self.executor,self.devices,probe=probe,candidates=candidates,sleep=lambda _:None,rediscovery_attempts=1,rediscovery_interval=0)
 def tearDown(self):self.tmp.cleanup()
 def test_disabled_session_cannot_execute(self):self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.session.result['state'],'hardware-validation-pending')
 def test_authenticated_activation_requires_session_credentials(self):
  preflight=Preflight();self.assertFalse(self.session.enableAuthenticatedTransport(Credentials(password=''),preflight));self.assertFalse(self.session.result['enabled'])
  with patch('firmware_update_session.AuthenticatedCameraTransport') as factory:
   transport=Transport();factory.return_value=transport;credentials=Credentials();self.assertTrue(self.session.enableAuthenticatedTransport(credentials,preflight));factory.assert_called_once_with(credentials);self.assertTrue(self.session.result['enabled']);self.assertNotIn('password',repr(self.session.result).lower())
 def test_authenticated_activation_requires_ready_preflight(self):
  credentials=Credentials();self.assertFalse(self.session.enableAuthenticatedTransport(credentials));self.assertFalse(self.session.enableAuthenticatedTransport(credentials,Preflight(False)));self.assertFalse(self.session.result['enabled'])
 def test_preflight_identity_must_still_match_live_device(self):
  credentials=Credentials();self.assertFalse(self.session.enableAuthenticatedTransport(credentials,Preflight(host='192.168.1.99')));self.assertFalse(self.session.result['enabled']);self.devices.items[0]['openipcIdentity']['sensor']='imx415';self.assertFalse(self.session.enableAuthenticatedTransport(credentials,Preflight()));self.assertFalse(self.session.result['enabled'])
 def test_disable_transport_returns_to_hardware_pending(self):
  self.assertTrue(self.session.configure_transport(Transport()));self.assertTrue(self.session.disableTransport());self.assertFalse(self.session.result['enabled']);self.assertEqual(self.session.result['state'],'hardware-validation-pending')
 def test_opt_in_transport_authenticates_then_fixed_upgrade(self):
  t=Transport();self.assertTrue(self.session.configure_transport(t));self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(t.calls,[('auth','192.168.1.50'),('run','192.168.1.50',['sysupgrade','-k','-r'])]);self.assertEqual(self.session.result['state'],'reboot-pending')
 def test_auth_failure_never_runs_sysupgrade(self):
  t=Transport(False);self.session.configure_transport(t);self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(t.calls,[('auth','192.168.1.50')])
 def test_transport_object_is_not_retained_by_session(self):
  t=Transport();self.session.configure_transport(t);self.assertNotIn('_transport',self.session.__dict__);self.assertNotIn('password',repr(self.session.result).lower())
 def test_active_transaction_rejects_transport_reconfiguration_and_reset(self):
  first=Transport();second=Transport();self.assertTrue(self.session.configure_transport(first));self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));before=dict(self.session.result);self.assertFalse(self.session.configure_transport(second));self.assertFalse(self.session.reset());self.assertTrue(self.executor.busy);self.assertEqual(self.executor.status['state'],'reboot-pending');self.assertEqual(self.session.result,before);self.assertEqual(second.calls,[])
 def test_live_host_mutation_does_not_replace_bound_reboot_host(self):
  t=Transport();self.session.configure_transport(t);self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.devices.items[0]['host']='not-an-ip';self.assertFalse(self.session.verifyAfterReboot());self.assertEqual(self.session.result['state'],'error');self.assertEqual(self.probe_calls,['192.168.1.50']);self.assertEqual(self.candidate_calls,['192.168.1.50'])
 def test_post_reboot_verification_uses_injected_network_boundaries(self):
  evidence={'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']}
  self.session._probe_provider=lambda host:(self.probe_calls.append(host) or evidence)
  t=Transport();self.session.configure_transport(t);self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertTrue(self.session.verifyAfterReboot());self.assertEqual(self.probe_calls,['192.168.1.50']);self.assertEqual(self.candidate_calls,['192.168.1.50']);self.assertEqual(self.session.result['state'],'verified')
if __name__=='__main__':unittest.main()
