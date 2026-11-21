import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
from firmware_executor import FirmwareExecutor
class Devices:
 def __init__(self):self.items=[{"id":"cam","openipcIdentity":{"verified":True,"platform":"ssc30kq","sensor":"imx335"}}]
class Adapter:
 def __init__(self):self.calls=[]
 def execute(self,*args):self.calls.append(args);return True
class ExecutorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/"fw.bin";self.image.write_bytes(b"safe-test");sha=hashlib.sha256(self.image.read_bytes()).hexdigest();self.center=FirmwareCenter(Devices());self.center.verifyImage(str(self.image),sha);self.center.precheck("cam","ssc30kq-imx335","upgrade",True,True);self.center.prepareExecution("cam","ssc30kq-imx335","upgrade")
 def tearDown(self):self.tmp.cleanup()
 def test_no_adapter_means_no_destructive_execution(self):
  x=FirmwareExecutor(self.center);self.assertFalse(x.execute("cam","ssc30kq-imx335","upgrade"));self.assertEqual(x.status["state"],"hardware-validation-pending")
 def test_artifact_change_blocks_executor_handoff(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.image.write_bytes(b"changed");self.assertFalse(x.execute("cam","ssc30kq-imx335","upgrade"));self.assertEqual(a.calls,[])
 def test_registered_adapter_requires_post_operation_verification(self):
  x=FirmwareExecutor(self.center);a=Adapter();x.register_adapter(a);self.assertTrue(x.execute("cam","ssc30kq-imx335","upgrade"));self.assertEqual(x.status["state"],"reboot-pending");self.assertTrue(x.completeVerification(True,True));self.assertEqual(x.status["state"],"verified")
if __name__=="__main__":unittest.main()
