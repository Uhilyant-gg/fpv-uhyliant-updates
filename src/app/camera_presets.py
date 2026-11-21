"""Versioned camera presets. Presets are device configuration, never per-stream video profiles."""
from PySide6.QtCore import QObject, Property, Signal, Slot
PRESETS={
 "ssc30kq-imx335-fpv-v1":{"id":"ssc30kq-imx335-fpv","version":1,"name":"SSC30KQ / IMX335 FPV","platform":"ssc30kq","sensor":"imx335","settings":{"role":"fpv","applyVideoProfile":False}}
}
class CameraPresets(QObject):
 changed=Signal()
 def __init__(self,devices):super().__init__();self.devices=devices;self._selected="";self._result={"ready":False,"reason":"Preset не вибрано","preset":{}}
 @Property("QVariantList",constant=True)
 def items(self):return [dict(v) for v in PRESETS.values()]
 @Property("QVariantMap",notify=changed)
 def result(self):return dict(self._result)
 @Slot(str,str,result=bool)
 def selectForDevice(self,key,device_id):
  p=PRESETS.get(key);d=next((x for x in self.devices.items if x.get("id")==device_id),None);identity=(d or {}).get("openipcIdentity") or {};ok=bool(p and d and identity.get("platform","").lower()==p["platform"] and identity.get("sensor","").lower()==p["sensor"])
  self._selected=key if ok else "";self._result={"ready":ok,"reason":"Preset сумісний з device identity" if ok else "Preset не сумісний або hardware identity unavailable","preset":dict(p) if p else {}};self.changed.emit();return ok
 @Slot(str,result=bool)
 def belongsToFirmware(self,key):
  p=PRESETS.get(key);return bool(p and p.get("settings",{}).get("applyVideoProfile") is False)
