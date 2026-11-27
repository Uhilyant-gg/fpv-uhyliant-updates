import unittest
from PySide6.QtCore import QObject,Signal
from telemetry_provider import CrsfProvider,MavlinkProvider,MspProvider,TelemetryRouter,NORMALIZED_FIELDS,unavailable_telemetry
class Runtime(QObject):
 changed=Signal()
 def __init__(self,telemetry=None,error=""):super().__init__();self.telemetry=telemetry or {};self.error=error
class Settings:
 def __init__(self,value=None):self.v=value
 def value(self,k,d=None):return self.v if self.v is not None else d
 def setValue(self,k,v):self.v=v
 def sync(self):pass
class TelemetryProviderTests(unittest.TestCase):
 def test_normalizes_without_inventing_values(self):
  p=MavlinkProvider(Runtime({'connected':True,'batteryVoltage':12.3}));t=p.telemetry;self.assertTrue(t['connected']);self.assertEqual(t['batteryVoltage'],12.3);self.assertIsNone(t['armed']);self.assertIsNone(t['gpsFix'])
 def test_preserves_field_freshness_for_overlay_presentation(self):
  t=MspProvider(Runtime({'connected':True,'altitude':12.0,'freshness':{'altitude':False}})).telemetry
  self.assertFalse(t['freshness']['altitude'])
 def test_missing_values_remain_unavailable_not_false_or_zero(self):
  t=MspProvider(Runtime()).telemetry
  for key in NORMALIZED_FIELDS:self.assertIsNone(t[key])
 def test_protocols_use_same_boundary(self):
  for cls in (MavlinkProvider,MspProvider,CrsfProvider):self.assertEqual(set(cls(Runtime()).telemetry)-{'provider'},set(NORMALIZED_FIELDS))
 def test_router_switches_without_changing_vehicle_contract(self):
  a=MavlinkProvider(Runtime({'connected':True,'armed':True}));b=MspProvider(Runtime({'connected':True,'armed':None}));r=TelemetryRouter([a,b],settings=Settings());self.assertTrue(r.select('MSP'));self.assertEqual(r.name,'MSP');self.assertIsNone(r.telemetry['armed'])
 def test_router_restores_saved_provider_and_ignores_invalid_saved_value(self):
  a=MavlinkProvider(Runtime());b=MspProvider(Runtime());self.assertEqual(TelemetryRouter([a,b],settings=Settings('MSP')).name,'MSP');self.assertEqual(TelemetryRouter([a,b],settings=Settings('bad')).name,'MAVLink')
 def test_unavailable_router_state_never_synthesizes_false_or_health(self):
  t=unavailable_telemetry('missing');self.assertEqual(t['provider'],'missing')
  for key in NORMALIZED_FIELDS:self.assertIsNone(t[key])
if __name__=='__main__':unittest.main()
