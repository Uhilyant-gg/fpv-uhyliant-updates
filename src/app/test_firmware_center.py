import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
class Devices:
    def __init__(self,identity):self.items=[{"id":"cam","openipcIdentity":identity}]
class FirmwareCenterTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/"firmware.bin";self.image.write_bytes(b"firmware-test-image");self.sha=hashlib.sha256(self.image.read_bytes()).hexdigest()
    def tearDown(self):self.tmp.cleanup()
    def center(self,identity):
        f=FirmwareCenter(Devices(identity));self.assertTrue(f.verifyImage(str(self.image),self.sha));return f
    def test_upgrade_requires_verified_existing_openipc(self):
        f=self.center({"verified":False,"platform":"ssc30kq","sensor":"imx335"});self.assertFalse(f.precheck("cam","ssc30kq-imx335","upgrade",True,True))
    def test_recovery_fullflash_requires_verified_existing_openipc(self):
        f=self.center({"verified":False,"platform":"ssc30kq","sensor":"imx335"});self.assertFalse(f.precheck("cam","ssc30kq-imx335","recovery-fullflash",True,True))
    def test_primary_is_separate_but_still_requires_observed_compatible_hardware(self):
        f=self.center({"verified":False,"platform":"ssc30kq","sensor":"imx335"});self.assertTrue(f.precheck("cam","ssc30kq-imx335","primary",True,True))
        bad=self.center({"verified":False,"platform":"ssc30kq","sensor":""});self.assertFalse(bad.precheck("cam","ssc30kq-imx335","primary",True,True))
    def test_hash_mismatch_blocks_all_modes(self):
        f=FirmwareCenter(Devices({"verified":True,"platform":"ssc30kq","sensor":"imx335"}));self.assertFalse(f.verifyImage(str(self.image),"0"*64));self.assertFalse(f.precheck("cam","ssc30kq-imx335","upgrade",True,True))
    def test_mode_policy_keeps_fullflash_non_primary(self):
        f=FirmwareCenter(Devices({}));self.assertFalse(f.modePolicy("primary")["requiresExistingOpenIPC"]);self.assertTrue(f.modePolicy("recovery-fullflash")["requiresExistingOpenIPC"])
if __name__=="__main__":unittest.main()
