import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
from firmware_update_session import FirmwareUpdateSession
class Devices:
 def __init__(self):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]
class Transport:
 def __init__(self,auth=True):self.auth=auth;self.calls=[]
 def authenticate(self,host):self.calls.append(('auth',host));return self.auth
 def run(self,host,argv):self.calls.append(('run',host,list(argv)));return True
class SessionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();image=Path(self.tmp.name)/'fw.bin';image.write_bytes(b'x');self.devices=Devices();center=FirmwareCenter(self.devices);center.verifyImage(str(image),hashlib.sha256(b'x').hexdigest());center.precheck('cam','ssc30kq-imx335','upgrade',True,True);center.prepareExecution('cam','ssc30kq-imx335','upgrade');self.executor=FirmwareExecutor(center);self.session=FirmwareUpdateSession(self.executor,self.devices)
 def tearDown(self):self.tmp.cleanup()
 def test_disabled_session_cannot_execute(self):self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(self.session.result['state'],'hardware-validation-pending')
 def test_opt_in_transport_authenticates_then_fixed_upgrade(self):
  t=Transport();self.session.configure_transport(t);self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(t.calls,[('auth','192.168.1.50'),('run','192.168.1.50',['sysupgrade','-k','-r'])]);self.assertEqual(self.session.result['state'],'reboot-pending')
 def test_auth_failure_never_runs_sysupgrade(self):
  t=Transport(False);self.session.configure_transport(t);self.assertFalse(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.assertEqual(t.calls,[('auth','192.168.1.50')])
 def test_transport_object_is_not_retained_by_session(self):
  t=Transport();self.session.configure_transport(t);self.assertNotIn('_transport',self.session.__dict__);self.assertNotIn('password',repr(self.session.result).lower())
 def test_invalid_post_reboot_host_fails_closed_without_probe(self):
  t=Transport();self.session.configure_transport(t);self.assertTrue(self.session.execute('cam','ssc30kq-imx335','upgrade'));self.devices.items[0]['host']='not-an-ip';self.assertFalse(self.session.verifyAfterReboot());self.assertEqual(self.session.result['state'],'error')
if __name__=='__main__':unittest.main()
