import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
class Devices:
 def __init__(self,identity):self.items=[{"id":"cam","openipcIdentity":identity}]
class FirmwareCenterTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/"firmware.bin";self.image.write_bytes(b"firmware-test-image");self.sha=hashlib.sha256(self.image.read_bytes()).hexdigest()
 def tearDown(self):self.tmp.cleanup()
 def center(self,identity):f=FirmwareCenter(Devices(identity));self.assertTrue(f.verifyImage(str(self.image),self.sha));return f
 def test_upgrade_requires_verified_existing_openipc(self):
  f=self.center({"verified":False,"platform":"ssc30kq","sensor":"imx335"});self.assertFalse(f.precheck("cam","ssc30kq-imx335","upgrade",True,True))
 def test_primary_is_separate_but_requires_observed_hardware(self):
  f=self.center({"verified":False,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","primary",True,True))
 def test_approval_bound_to_inputs(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","upgrade",True,True));self.assertTrue(f.approvalMatches("cam","ssc30kq-imx335","upgrade"));self.assertFalse(f.approvalMatches("cam","ssc30kq-imx335","primary"))
 def test_execution_plan_requires_matching_approval(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertFalse(f.prepareExecution("cam","ssc30kq-imx335","upgrade"));self.assertTrue(f.precheck("cam","ssc30kq-imx335","upgrade",True,True));self.assertTrue(f.prepareExecution("cam","ssc30kq-imx335","upgrade"));self.assertTrue(f.executionPlan["ready"]);self.assertIn("Rediscover device",f.executionPlan["steps"]);self.assertIn("Verify OpenIPC identity and firmware",f.executionPlan["steps"])
 def test_fullflash_plan_explicitly_requires_verified_custom_openipc(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","recovery-fullflash",True,True));self.assertTrue(f.prepareExecution("cam","ssc30kq-imx335","recovery-fullflash"));self.assertTrue(any("verified custom OpenIPC" in step for step in f.executionPlan["steps"]))
if __name__=="__main__":unittest.main()
