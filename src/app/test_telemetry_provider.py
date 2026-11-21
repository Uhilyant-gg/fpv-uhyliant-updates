import unittest
from PySide6.QtCore import QObject, Signal
from telemetry_provider import CrsfProvider, MavlinkProvider, MspProvider, TelemetryRouter

class FakeRuntime(QObject):
    changed=Signal()
    def __init__(self,voltage=15.2):
        super().__init__();self.telemetry={"connected":True,"armed":False,"batteryVoltage":voltage,"unexpected":123};self.error=""

class TelemetryProviderTests(unittest.TestCase):
    def test_normalizes_without_inventing_values(self):
        provider=MavlinkProvider(FakeRuntime());telemetry=provider.telemetry
        self.assertEqual(telemetry["provider"],"MAVLink");self.assertEqual(telemetry["batteryVoltage"],15.2);self.assertIsNone(telemetry["gpsFix"]);self.assertNotIn("unexpected",telemetry);self.assertTrue(provider.readOnly);self.assertTrue(provider.available)
    def test_protocols_use_same_boundary(self):
        self.assertEqual(MspProvider(FakeRuntime()).telemetry["provider"],"MSP");self.assertEqual(CrsfProvider(FakeRuntime()).telemetry["provider"],"CRSF")
    def test_router_switches_without_changing_vehicle_contract(self):
        mav=MavlinkProvider(FakeRuntime(15.2));msp=MspProvider(FakeRuntime(16.1));crsf=CrsfProvider(FakeRuntime(14.8));router=TelemetryRouter([mav,msp,crsf])
        self.assertEqual(router.name,"MAVLink");self.assertEqual(router.telemetry["batteryVoltage"],15.2)
        self.assertTrue(router.select("MSP"));self.assertEqual(router.name,"MSP");self.assertEqual(router.telemetry["batteryVoltage"],16.1);self.assertTrue(router.readOnly)
        self.assertFalse(router.select("unknown"));self.assertEqual(router.name,"MSP")

if __name__=="__main__":unittest.main()
