import unittest
from firmware_center import FirmwareCenter
class Devices:
    def __init__(self,identity):self.items=[{"id":"cam","openipcIdentity":identity}]
class FirmwareCenterTests(unittest.TestCase):
    def test_ssc30kq_imx335_requires_all_destructive_safety_gates(self):
        f=FirmwareCenter(Devices({"verified":True,"platform":"ssc30kq","sensor":"imx335"}))
        self.assertFalse(f.precheck("cam","ssc30kq-imx335","upgrade",False,True,True));self.assertEqual(f.result["reason"],"Destructive flashing заблоковано")
        self.assertTrue(f.precheck("cam","ssc30kq-imx335","upgrade",True,True,True))
    def test_wrong_sensor_is_rejected(self):
        f=FirmwareCenter(Devices({"verified":True,"platform":"ssc30kq","sensor":"imx415"}));self.assertFalse(f.precheck("cam","ssc30kq-imx335","upgrade",True,True,True))
    def test_generic_onvif_cannot_use_fullflash(self):
        f=FirmwareCenter(Devices({"verified":False,"platform":"ssc30kq","sensor":"imx335"}));self.assertFalse(f.precheck("cam","ssc30kq-imx335","recovery-fullflash",True,True,True));self.assertFalse(next(c for c in f.result["checks"] if c["name"]=="fullflash")["ok"])
if __name__=="__main__":unittest.main()
