"""Guarded firmware executor boundary. Destructive hardware work requires an explicit adapter."""
import hashlib
from PySide6.QtCore import QObject, Property, Signal, Slot
from firmware_center import SUPPORTED_PROFILES
from post_flash_verify import verify_post_flash
class FirmwareExecutor(QObject):
 changed=Signal()
 def __init__(self,firmware_center):super().__init__();self.center=firmware_center;self._adapter=None;self._locked_device="";self._before={};self._state=self._idle()
 def _idle(self):return {"state":"idle","deviceId":"","profile":"","mode":"","step":"","error":"","verification":{},"hardwareValidation":"hardware-validation-pending"}
 @Property("QVariantMap",notify=changed)
 def status(self):return dict(self._state)
 @Property(bool,notify=changed)
 def busy(self):return bool(self._locked_device)
 def register_adapter(self,adapter):self._adapter=adapter
 def _device(self,did):return next((d for d in self.center.devices.items if d.get("id")==did),None)
 def _set(self,state,**extra):self._state={**self._state,"state":state,**extra};self.changed.emit()
 def _rehash(self):
  a=self.center.artifact
  try:
   h=hashlib.sha256()
   with open(a.get("path",""),"rb") as f:
    for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
   return bool(a.get("sha256") and h.hexdigest()==a["sha256"])
  except OSError:return False
 @Slot(str,str,str,result=bool)
 def execute(self,device_id,profile,mode):
  if self._locked_device:self._set("blocked",error="Інша firmware operation вже активна");return False
  if not self.center.executionPlan.get("ready") or not self.center.approvalMatches(device_id,profile,mode):self._set("blocked",error="Execution plan або immutable approval невалідний");return False
  if not self._rehash():self._set("blocked",error="Firmware SHA-256 змінився після pre-check");return False
  device=self._device(device_id);self._before=dict((device or {}).get("openipcIdentity") or {})
  if self._adapter is None:self._set("hardware-validation-pending",deviceId=device_id,profile=profile,mode=mode,step="executor",error="Hardware executor adapter не підключений");return False
  self._locked_device=device_id;self._set("executing",deviceId=device_id,profile=profile,mode=mode,step="flash",error="",verification={})
  try:
   ok=bool(self._adapter.execute(device_id,profile,mode,self.center.artifact,self.center.executionPlan));self._set("reboot-pending" if ok else "error",step="rediscover" if ok else "flash",error="" if ok else "Executor повідомив про помилку");return ok
  except Exception as exc:self._set("error",step="flash",error=str(exc));return False
  finally:self._locked_device="";self.changed.emit()
 @Slot("QVariantMap",str,result=bool)
 def verifyObserved(self,observed,expected_firmware=""):
  if self._state.get("state")!="reboot-pending":return False
  profile=SUPPORTED_PROFILES.get(self._state.get("profile"),{});result=verify_post_flash(self._before,dict(observed or {}),profile,expected_firmware);self._set("verified" if result["ok"] else "error",step="verify",verification=result,error="" if result["ok"] else "Post-operation verification failed");return bool(result["ok"])
 @Slot(bool,bool,result=bool)
 def completeVerification(self,rediscovered,identity_verified):
  if self._state.get("state")!="reboot-pending":return False
  ok=bool(rediscovered and identity_verified);self._set("verified" if ok else "error",step="verify",error="" if ok else "Post-operation verification failed");return ok
 @Slot()
 def reset(self):
  if not self._locked_device:self._before={};self._state=self._idle();self.changed.emit()
