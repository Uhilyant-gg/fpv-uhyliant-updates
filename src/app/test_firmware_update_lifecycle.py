import hashlib,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
from firmware_update_lifecycle import FirmwareUpdateLifecycle
from firmware_rediscovery import FirmwareRediscovery
class Devices:
 def __init__(self):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]
class Adapter:
 def execute(self,*args):return True
class ContextExecutor:
 def __init__(self,context):self.context=deepcopy(context);self._nonce=None;self.state='reboot-pending'
 def beginRediscovery(self):
  if self.state!='reboot-pending':return None
  self._nonce=object();self.state='rediscovering';return deepcopy(self.context),self._nonce
 def failRediscovery(self,nonce=None):
  if self.state=='rediscovering' and nonce is not self._nonce:return False
  self.state='error';return False
 def acceptRediscoveredVerification(self,result,verification,nonce=None):
  if self.state!='rediscovering' or nonce is not self._nonce:return False
  self.state='verified' if verification.get('ok') is True else 'error';return verification.get('ok') is True
class Tests(unittest.TestCase):
 def make(self,probe,candidates=None):
  td=tempfile.TemporaryDirectory();image=Path(td.name)/'fw.bin';image.write_bytes(b'x');devices=Devices();center=FirmwareCenter(devices);center.verifyImage(str(image),hashlib.sha256(b'x').hexdigest());center.precheck('cam','ssc30kq-imx335','upgrade',True,True);center.prepareExecution('cam','ssc30kq-imx335','upgrade');executor=FirmwareExecutor(center);executor.register_adapter(Adapter());self.assertTrue(executor.execute('cam','ssc30kq-imx335','upgrade'));return td,executor,FirmwareUpdateLifecycle(executor,FirmwareRediscovery(probe,sleep=lambda _:None,candidates=candidates))
 def test_fresh_verified_openipc_completes_with_observed_firmware(self):
  td,x,l=self.make(lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']})
  try:self.assertTrue(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'verified')
  finally:td.cleanup()
 def test_dhcp_changed_host_completes_only_after_identity_match(self):
  def probe(host):
   if host=='192.168.1.60':return {'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx415','firmware':'other'},'evidence':['OpenIPC status.cgi']}
   if host=='192.168.1.70':return {'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['OpenIPC status.cgi']}
   return {}
  td,x,l=self.make(probe,lambda old:['192.168.1.60','192.168.1.70'])
  try:self.assertTrue(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'verified');self.assertEqual(x.status['verification']['rediscoveredHost'],'192.168.1.70')
  finally:td.cleanup()
 def test_only_wrong_camera_fails_closed(self):
  result={'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx415','firmware':'new'},'evidence':['OpenIPC status.cgi']};td,x,l=self.make(lambda host:result,lambda old:['192.168.1.60'])
  try:self.assertFalse(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'error')
  finally:td.cleanup()
 def test_missing_firmware_is_rejected(self):
  td,x,l=self.make(lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335'},'evidence':['OpenIPC status.cgi']})
  try:self.assertFalse(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'error')
  finally:td.cleanup()
 def test_non_private_original_host_fails_before_probe(self):
  calls=[];x=ContextExecutor({'host':'8.8.8.8','profile':'ssc30kq-imx335','before':{'platform':'ssc30kq','sensor':'imx335','firmware':'old'}});l=FirmwareUpdateLifecycle(x,FirmwareRediscovery(lambda host:(calls.append(host) or {}),sleep=lambda _:None))
  self.assertFalse(l.verify_after_reboot(1,0));self.assertEqual(x.state,'error');self.assertEqual(calls,[])
 def test_missing_pre_update_hardware_identity_fails_before_rediscovery(self):
  calls=[];x=ContextExecutor({'host':'192.168.1.50','profile':'ssc30kq-imx335','before':{'platform':'ssc30kq','sensor':'','firmware':'old'}});l=FirmwareUpdateLifecycle(x,FirmwareRediscovery(lambda host:(calls.append(host) or {}),sleep=lambda _:None))
  self.assertFalse(l.verify_after_reboot(1,0));self.assertEqual(x.state,'error');self.assertEqual(calls,[])
if __name__=='__main__':unittest.main()
