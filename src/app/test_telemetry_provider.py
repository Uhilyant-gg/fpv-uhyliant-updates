import unittest
from PySide6.QtCore import QObject, Signal
from telemetry_provider import CrsfProvider, MavlinkProvider, MspProvider, TelemetryRouter

class FakeRuntime(QObject):
    changed=Signal()
    def __init__(self,voltage=15.2,telemetry=None):
        super().__init__();self.telemetry=telemetry if telemetry is not None else {"connected":True,"armed":False,"batteryVoltage":voltage,"unexpected":123};self.error=""

class FakeSettings:
    def __init__(self,values=None):self.values=dict(values or {});self.synced=False
    def value(self,key,default=None):return self.values.get(key,default)
    def setValue(self,key,value):self.values[key]=value
    def sync(self):self.synced=True

class TelemetryProviderTests(unittest.TestCase):
    def test_normalizes_without_inventing_values(self):
        provider=MavlinkProvider(FakeRuntime());telemetry=provider.telemetry
        self.assertEqual(telemetry["provider"],"MAVLink");self.assertEqual(telemetry["batteryVoltage"],15.2);self.assertIsNone(telemetry["gpsFix"]);self.assertNotIn("unexpected",telemetry);self.assertTrue(provider.readOnly);self.assertTrue(provider.available)
    def test_missing_values_remain_unavailable_not_false_or_zero(self):
        provider=MspProvider(FakeRuntime(telemetry={"connected":False}));telemetry=provider.telemetry
        self.assertFalse(telemetry["connected"]);self.assertIsNone(telemetry["armed"]);self.assertIsNone(telemetry["batteryVoltage"]);self.assertIsNone(telemetry["gpsFix"]);self.assertFalse(provider.available)
    def test_protocols_use_same_boundary(self):
        self.assertEqual(MspProvider(FakeRuntime()).telemetry["provider"],"MSP");self.assertEqual(CrsfProvider(FakeRuntime()).telemetry["provider"],"CRSF")
    def test_router_switches_without_changing_vehicle_contract(self):
        settings=FakeSettings();mav=MavlinkProvider(FakeRuntime(15.2));msp=MspProvider(FakeRuntime(16.1));crsf=CrsfProvider(FakeRuntime(14.8));router=TelemetryRouter([mav,msp,crsf],settings=settings)
        self.assertEqual(router.name,"MAVLink");self.assertEqual(router.telemetry["batteryVoltage"],15.2)
        self.assertTrue(router.select("MSP"));self.assertEqual(router.name,"MSP");self.assertEqual(router.telemetry["batteryVoltage"],16.1);self.assertTrue(router.readOnly);self.assertEqual(settings.values[TelemetryRouter.SETTINGS_KEY],"MSP");self.assertTrue(settings.synced)
        self.assertFalse(router.select("unknown"));self.assertEqual(router.name,"MSP")
    def test_router_restores_saved_provider_and_ignores_invalid_saved_value(self):
        providers=[MavlinkProvider(FakeRuntime()),MspProvider(FakeRuntime()),CrsfProvider(FakeRuntime())]
        self.assertEqual(TelemetryRouter(providers,settings=FakeSettings({TelemetryRouter.SETTINGS_KEY:"CRSF"})).name,"CRSF")
        self.assertEqual(TelemetryRouter(providers,settings=FakeSettings({TelemetryRouter.SETTINGS_KEY:"invalid"})).name,"MAVLink")

if __name__=="__main__":unittest.main()
