"""Guarded firmware executor boundary.
No hardware adapter is registered by default, therefore this module cannot perform a destructive write.
"""
import hashlib
from PySide6.QtCore import QObject, Property, Signal, Slot

class FirmwareExecutor(QObject):
    changed=Signal()
    def __init__(self,firmware_center):
        super().__init__();self.center=firmware_center;self._adapter=None;self._locked_device="";self._state=self._idle()
    def _idle(self):return {"state":"idle","deviceId":"","profile":"","mode":"","step":"","error":"","hardwareValidation":"hardware-validation-pending"}
    @Property("QVariantMap",notify=changed)
    def status(self):return dict(self._state)
    @Property(bool,notify=changed)
    def busy(self):return bool(self._locked_device)
    def register_adapter(self,adapter):self._adapter=adapter
    def _set(self,state,**extra):self._state={**self._state,"state":state,**extra};self.changed.emit()
    def _rehash(self):
        artifact=self.center.artifact;path=artifact.get("path","");expected=artifact.get("sha256","")
        try:
            h=hashlib.sha256()
            with open(path,"rb") as f:
                for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
            return bool(expected and h.hexdigest()==expected)
        except OSError:return False
    @Slot(str,str,str,result=bool)
    def execute(self,device_id,profile,mode):
        if self._locked_device:self._set("blocked",error="Інша firmware operation вже активна");return False
        if not self.center.executionPlan.get("ready") or not self.center.approvalMatches(device_id,profile,mode):self._set("blocked",error="Execution plan або immutable approval невалідний");return False
        if not self._rehash():self._set("blocked",error="Firmware SHA-256 змінився після pre-check");return False
        if self._adapter is None:self._set("hardware-validation-pending",deviceId=device_id,profile=profile,mode=mode,step="executor",error="Hardware executor adapter не підключений");return False
        self._locked_device=device_id;self._set("executing",deviceId=device_id,profile=profile,mode=mode,step="flash",error="")
        try:
            ok=bool(self._adapter.execute(device_id,profile,mode,self.center.artifact,self.center.executionPlan))
            self._set("reboot-pending" if ok else "error",step="reboot" if ok else "flash",error="" if ok else "Executor повідомив про помилку");return ok
        except Exception as exc:self._set("error",step="flash",error=str(exc));return False
        finally:self._locked_device="";self.changed.emit()
    @Slot(bool,bool,result=bool)
    def completeVerification(self,rediscovered,identity_verified):
        if self._state.get("state")!="reboot-pending":return False
        ok=bool(rediscovered and identity_verified);self._set("verified" if ok else "error",step="verify",error="" if ok else "Post-operation verification failed");return ok
    @Slot()
    def reset(self):
        if not self._locked_device:self._state=self._idle();self.changed.emit()
