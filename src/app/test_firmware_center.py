import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from firmware_center import FirmwareCenter
class Devices:
 def __init__(self,identity):self.items=[{"id":"cam","host":"192.168.1.50","openipcIdentity":identity}]
class FirmwareCenterTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/"firmware.bin";self.image.write_bytes(b"firmware-test-image");self.sha=hashlib.sha256(self.image.read_bytes()).hexdigest()
 def tearDown(self):self.tmp.cleanup()
 def center(self,identity):f=FirmwareCenter(Devices(identity));self.assertTrue(f.verifyImage(str(self.image),self.sha));return f
 def test_upgrade_requires_verified_existing_openipc(self):
  f=self.center({"verified":False,"platform":"ssc30kq","sensor":"imx335"});self.assertFalse(f.precheck("cam","ssc30kq-imx335","upgrade",False,False))
 def test_normal_upgrade_does_not_require_recovery_or_layout(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","upgrade",False,False));names=[x["name"] for x in f.result["checks"]];self.assertNotIn("recovery",names);self.assertNotIn("layout",names)
 def test_primary_and_fullflash_keep_recovery_and_layout_gates(self):
  f=self.center({"verified":False,"platform":"ssc30kq","sensor":"imx335"});self.assertFalse(f.precheck("cam","ssc30kq-imx335","primary",False,False));self.assertTrue(f.precheck("cam","ssc30kq-imx335","primary",True,True));f.devices.items[0]["openipcIdentity"]["verified"]=True;self.assertFalse(f.precheck("cam","ssc30kq-imx335","recovery-fullflash",False,False))
 def test_compatible_profile_is_derived_only_from_observed_identity(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertEqual(f.compatibleProfile("cam"),"ssc30kq-imx335");f.devices.items[0]["openipcIdentity"]["sensor"]="unknown";self.assertEqual(f.compatibleProfile("cam"),"")
 def test_automatic_upgrade_prepares_plan_without_manual_recovery_flags(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.prepareAutomaticUpgrade("cam"));self.assertTrue(f.executionPlan["ready"]);self.assertEqual(f.result["mode"],"upgrade")
 def test_upgrade_readiness_uses_observed_identity(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335","firmware":"v1"});r=f.upgradeReadiness("cam");self.assertTrue(r["ready"]);self.assertEqual(r["currentFirmware"],"v1");self.assertEqual(r["argv"],["sysupgrade","-k","-r"])
 def test_approval_bound_to_inputs(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","upgrade",False,False));self.assertTrue(f.approvalMatches("cam","ssc30kq-imx335","upgrade"));self.assertFalse(f.approvalMatches("cam","ssc30kq-imx335","primary"))
 def test_host_change_invalidates_approval_and_execution_plan(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","upgrade",False,False));f.devices.items[0]["host"]="192.168.1.99";self.assertFalse(f.approvalMatches("cam","ssc30kq-imx335","upgrade"));self.assertFalse(f.prepareExecution("cam","ssc30kq-imx335","upgrade"));self.assertFalse(f.executionPlan["ready"])
 def test_unreadable_firmware_file_has_a_human_error_without_path_details(self):
  f=FirmwareCenter(Devices({"verified":True,"platform":"ssc30kq","sensor":"imx335"}))
  with patch.object(Path,"open",side_effect=PermissionError("C:\\private\\firmware.bin: access denied")):
   self.assertFalse(f.verifyImage(str(self.image),self.sha))
  error=f.artifact["error"]
  self.assertIn("Перевірте доступ до файлу",error)
  self.assertNotIn("PermissionError",error)
  self.assertNotIn(str(self.image),error)
 def test_execution_plan_requires_matching_approval(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertFalse(f.prepareExecution("cam","ssc30kq-imx335","upgrade"));self.assertTrue(f.precheck("cam","ssc30kq-imx335","upgrade",False,False));self.assertTrue(f.prepareExecution("cam","ssc30kq-imx335","upgrade"));self.assertTrue(f.executionPlan["ready"]);self.assertIn("Повторно виявити пристрій",f.executionPlan["steps"]);self.assertIn("Перевірити ідентичність OpenIPC і прошивку",f.executionPlan["steps"])
 def test_fullflash_plan_explicitly_requires_verified_custom_openipc(self):
  f=self.center({"verified":True,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","recovery-fullflash",True,True));self.assertTrue(f.prepareExecution("cam","ssc30kq-imx335","recovery-fullflash"));self.assertTrue(any("підтвердженої кастомної OpenIPC" in step for step in f.executionPlan["steps"]))
if __name__=="__main__":unittest.main()
