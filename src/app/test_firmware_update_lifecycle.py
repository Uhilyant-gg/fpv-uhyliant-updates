import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
from firmware_update_lifecycle import FirmwareUpdateLifecycle
from firmware_rediscovery import FirmwareRediscovery
class Devices:
 def __init__(self):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335','firmware':'old','evidence':['Majestic /api/v1/config.json']}}]
class Adapter:
 def execute(self,*args):return True
class Tests(unittest.TestCase):
 def make(self,probe):
  td=tempfile.TemporaryDirectory();image=Path(td.name)/'fw.bin';image.write_bytes(b'x');devices=Devices();center=FirmwareCenter(devices);center.verifyImage(str(image),hashlib.sha256(b'x').hexdigest());center.precheck('cam','ssc30kq-imx335','upgrade',True,True);center.prepareExecution('cam','ssc30kq-imx335','upgrade');executor=FirmwareExecutor(center);executor.register_adapter(Adapter());self.assertTrue(executor.execute('cam','ssc30kq-imx335','upgrade'));return td,executor,FirmwareUpdateLifecycle(executor,FirmwareRediscovery(probe,sleep=lambda _:None))
 def test_fresh_verified_openipc_completes_with_observed_firmware(self):
  td,x,l=self.make(lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335','firmware':'new'},'evidence':['Majestic /api/v1/config.json']})
  try:self.assertTrue(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'verified');self.assertEqual(x.status['verification']['identity']['firmware'],'new')
  finally:td.cleanup()
 def test_generic_reachable_host_cannot_complete(self):
  td,x,l=self.make(lambda host:{'reachable':True,'openipc':False})
  try:self.assertFalse(l.verify_after_reboot(2,0));self.assertEqual(x.status['state'],'error')
  finally:td.cleanup()
 def test_changed_hardware_is_rejected(self):
  td,x,l=self.make(lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx415','firmware':'new'},'evidence':['Majestic /api/v1/config.json']})
  try:self.assertFalse(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'error')
  finally:td.cleanup()
 def test_partial_post_reboot_hardware_is_rejected(self):
  for identity in ({'platform':'ssc30kq','firmware':'new'},{'sensor':'imx335','firmware':'new'}):
   td,x,l=self.make(lambda host,i=identity:{'openipc':True,'identity':i,'evidence':['Majestic /api/v1/config.json']})
   try:self.assertFalse(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'error')
   finally:td.cleanup()
 def test_missing_observed_firmware_is_rejected(self):
  td,x,l=self.make(lambda host:{'openipc':True,'identity':{'platform':'ssc30kq','sensor':'imx335'},'evidence':['OpenIPC status.cgi']})
  try:self.assertFalse(l.verify_after_reboot(1,0));self.assertEqual(x.status['state'],'error')
  finally:td.cleanup()
 def test_sysupgrade_dispatch_remains_reboot_pending_until_rediscovery(self):
  td,x,l=self.make(lambda host:None)
  try:self.assertEqual(x.status['state'],'reboot-pending')
  finally:td.cleanup()
if __name__=='__main__':unittest.main()
