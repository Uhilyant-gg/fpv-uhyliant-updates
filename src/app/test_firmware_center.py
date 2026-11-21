import hashlib,tempfile,unittest
from pathlib import Path
from firmware_center import FirmwareCenter
class Devices:
    def __init__(self,identity):self.items=[{"id":"cam","openipcIdentity":identity}]
class FirmwareCenterTests(unittest.TestCase):
    def setUp(self):self.f=FirmwareCenter(Devices({"verified":True,"platform":"ssc30kq","sensor":"imx335"}));self.tmp=tempfile.TemporaryDirectory();self.image=Path(self.tmp.name)/"firmware.bin";self.image.write_bytes(b"firmware-test-image");self.sha=hashlib.sha256(self.image.read_bytes()).hexdigest()
    def tearDown(self):self.tmp.cleanup()
    def test_image_hash_must_match_before_precheck(self):
        self.assertFalse(self.f.precheck("cam","ssc30kq-imx335","upgrade",True,True));self.assertFalse(self.f.verifyImage(str(self.image),"0"*64));self.assertFalse(self.f.artifact["verified"]);self.assertTrue(self.f.verifyImage(str(self.image),self.sha));self.assertTrue(self.f.precheck("cam","ssc30kq-imx335","upgrade",True,True));self.assertEqual(self.f.result["artifactSha256"],self.sha)
    def test_wrong_sensor_is_rejected(self):
        f=FirmwareCenter(Devices({"verified":True,"platform":"ssc30kq","sensor":"imx415"}));f.verifyImage(str(self.image),self.sha);self.assertFalse(f.precheck("cam","ssc30kq-imx335","upgrade",True,True))
    def test_generic_onvif_cannot_use_fullflash(self):
        f=FirmwareCenter(Devices({"verified":False,"platform":"ssc30kq","sensor":"imx335"}));f.verifyImage(str(self.image),self.sha);self.assertFalse(f.precheck("cam","ssc30kq-imx335","recovery-fullflash",True,True));self.assertFalse(next(c for c in f.result["checks"] if c["name"]=="fullflash")["ok"])
if __name__=="__main__":unittest.main()
