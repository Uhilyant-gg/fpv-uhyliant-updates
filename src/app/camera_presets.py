"""Versioned camera presets. Presets are device configuration, never per-stream video profiles."""
from copy import deepcopy
from PySide6.QtCore import QObject, Property, Signal, Slot

PRESETS={
 "ssc30kq-imx335-fpv-v1":{
  "key":"ssc30kq-imx335-fpv-v1","id":"ssc30kq-imx335-fpv","version":1,"name":"SSC30KQ / IMX335 FPV",
  "platform":"ssc30kq","sensor":"imx335",
  "settings":{"role":"fpv","orientation":"normal"}
 },
 "ssc30kq-imx335-fpv-inverted-v1":{
  "key":"ssc30kq-imx335-fpv-inverted-v1","id":"ssc30kq-imx335-fpv-inverted","version":1,"name":"SSC30KQ / IMX335 FPV · inverted",
  "platform":"ssc30kq","sensor":"imx335",
  "settings":{"role":"fpv","orientation":"rotate_180"}
 }
}

def compatible(preset,identity):
 return bool(preset and identity and identity.get("verified") is True and identity.get("platform","").lower()==preset["platform"] and identity.get("sensor","").lower()==preset["sensor"])

def public_preset(preset):
 if not preset:return {}
 p=deepcopy(preset);p["settings"]["applyVideoProfile"]=False;return p

class CameraPresets(QObject):
 changed=Signal()
 def __init__(self,devices):super().__init__();self.devices=devices;self._selected="";self._device_id="";self._result={"ready":False,"reason":"Preset не вибрано","preset":{},"plan":{}}
 @Property("QVariantList",constant=True)
 def items(self):return [public_preset(v) for v in PRESETS.values()]
 @Property("QVariantMap",notify=changed)
 def result(self):return deepcopy(self._result)
 def _device(self,device_id):return next((x for x in self.devices.items if x.get("id")==device_id),None)
 def _set_result(self,ready,reason,preset=None,plan=None):self._result={"ready":bool(ready),"reason":reason,"preset":public_preset(preset),"plan":deepcopy(plan or {})};self.changed.emit()
 @Slot(str,str,result=bool)
 def selectForDevice(self,key,device_id):
  p=PRESETS.get(key);d=self._device(device_id);identity=(d or {}).get("openipcIdentity") or {};ok=compatible(p,identity)
  self._selected=key if ok else "";self._device_id=device_id if ok else ""
  self._set_result(ok,"Preset сумісний з verified device identity" if ok else "Preset не сумісний або verified hardware identity unavailable",p)
  return ok
 @Slot(result='QVariantMap')
 def buildApplyPlan(self):
  p=PRESETS.get(self._selected);d=self._device(self._device_id);identity=(d or {}).get("openipcIdentity") or {}
  if not compatible(p,identity):self._selected="";self._device_id="";self._set_result(False,"Preset selection більше не відповідає verified hardware identity",p);return {}
  plan={"deviceId":self._device_id,"presetId":p["id"],"presetVersion":p["version"],"platform":p["platform"],"sensor":p["sensor"],"settings":deepcopy(p["settings"]),"appliesVideoProfile":False,"execution":"hardware-validation-pending"}
  self._set_result(True,"Camera preset apply plan готовий; hardware executor не підключений",p,plan);return deepcopy(plan)
 @Slot(str,result=bool)
 def belongsToFirmware(self,key):return False
 @Slot(str,result=bool)
 def affectsVideoProfile(self,key):return False
