"""Safety gates and immutable firmware artifact verification for OpenIPC operations.
No destructive flashing is performed here.
"""
import hashlib
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot

SUPPORTED_PROFILES={"ssc30kq-imx335":{"platform":"ssc30kq","sensor":"imx335","modes":{"primary":{"requiresExistingOpenIPC":False},"upgrade":{"requiresExistingOpenIPC":True},"recovery-fullflash":{"requiresExistingOpenIPC":True}}}}
MODES=("primary","upgrade","recovery-fullflash")

class FirmwareCenter(QObject):
    changed=Signal()
    def __init__(self,devices):super().__init__();self.devices=devices;self._artifact=self._empty_artifact();self._result=self._empty()
    def _empty(self):return {"ready":False,"deviceId":"","profile":"","mode":"","checks":[],"reason":"Не виконано pre-check","approvalToken":""}
    def _empty_artifact(self):return {"path":"","sha256":"","expectedSha256":"","size":0,"verified":False,"error":"Firmware image не вибрано"}
    @Property("QVariantMap",notify=changed)
    def result(self):return dict(self._result)
    @Property("QVariantMap",notify=changed)
    def artifact(self):return dict(self._artifact)
    @Property("QStringList",constant=True)
    def profiles(self):return list(SUPPORTED_PROFILES)
    @Property("QStringList",constant=True)
    def modes(self):return list(MODES)
    @Slot(str,result="QVariantMap")
    def modePolicy(self,mode):
        if mode=="primary":return {"title":"Primary installation","requiresExistingOpenIPC":False,"description":"Первинна установка. Не використовує recovery/fullflash як універсальний метод."}
        if mode=="upgrade":return {"title":"Upgrade","requiresExistingOpenIPC":True,"description":"Оновлення лише для verified сумісного OpenIPC пристрою."}
        if mode=="recovery-fullflash":return {"title":"Recovery / fullflash","requiresExistingOpenIPC":True,"description":"Recovery/fullflash лише для пристрою з verified сумісним custom OpenIPC."}
        return {"title":"Unknown","requiresExistingOpenIPC":True,"description":"Невідомий режим заблоковано."}
    def _invalidate(self,reason="Вхідні дані змінилися; повторіть pre-check"):
        if self._result.get("ready") or self._result.get("approvalToken"):
            self._result={**self._result,"ready":False,"reason":reason,"approvalToken":""}
    @Slot(str,str,result=bool)
    def verifyImage(self,path,expected_sha256):
        self._invalidate();expected=expected_sha256.strip().lower();p=Path(path.strip())
        if not p.is_file():self._artifact={"path":str(p),"sha256":"","expectedSha256":expected,"size":0,"verified":False,"error":"Firmware image не знайдено"};self.changed.emit();return False
        h=hashlib.sha256();size=0
        try:
            with p.open("rb") as f:
                for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk);size+=len(chunk)
        except OSError as exc:self._artifact={"path":str(p),"sha256":"","expectedSha256":expected,"size":0,"verified":False,"error":str(exc)};self.changed.emit();return False
        actual=h.hexdigest();valid_expected=len(expected)==64 and all(c in "0123456789abcdef" for c in expected);verified=valid_expected and actual==expected
        self._artifact={"path":str(p),"sha256":actual,"expectedSha256":expected,"size":size,"verified":verified,"error":"" if verified else ("Некоректний expected SHA-256" if not valid_expected else "SHA-256 не збігається")};self.changed.emit();return verified
    def _approval_token(self,device_id,profile,mode,identity):
        material="|".join((device_id,profile,mode,self._artifact["sha256"],str(self._artifact["size"]),str(identity.get("platform","")).lower(),str(identity.get("sensor","")).lower(),str(bool(identity.get("verified")))))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()
    @Slot(str,str,str,bool,bool,result=bool)
    def precheck(self,device_id,profile,mode,recovery_ready,layout_verified):
        device=next((d for d in self.devices.items if d.get("id")==device_id),None);identity=(device or {}).get("openipcIdentity") or {};target=SUPPORTED_PROFILES.get(profile);checks=[];policy=self.modePolicy(mode)
        def add(name,ok,detail):checks.append({"name":name,"ok":bool(ok),"detail":detail})
        add("device",device is not None,"Пристрій знайдено" if device else "Пристрій не знайдено")
        add("profile",target is not None,"Firmware profile відомий" if target else "Невідомий firmware profile")
        observed=bool(identity.get("platform") and identity.get("sensor"));compatible=bool(target and observed and identity.get("platform","").lower()==target["platform"] and identity.get("sensor","").lower()==target["sensor"]);add("hardware",compatible,"Platform/sensor відповідають profile" if compatible else "Platform/sensor не підтверджують сумісність")
        existing_required=bool(policy.get("requiresExistingOpenIPC",True));openipc_ok=bool(identity.get("verified")) if existing_required else True;add("existing-openipc",openipc_ok,"Verified existing OpenIPC" if existing_required and openipc_ok else ("Existing OpenIPC не є вимогою primary installation" if not existing_required else "Existing OpenIPC не підтверджено"))
        add("layout",layout_verified,"Flash layout перевірено" if layout_verified else "Flash layout не перевірено")
        add("image",self._artifact["verified"],"SHA-256 firmware image перевірено" if self._artifact["verified"] else (self._artifact["error"] or "Firmware image не перевірено"))
        add("recovery",recovery_ready,"Recovery path готовий" if recovery_ready else "Recovery path не підтверджено")
        mode_ok=mode in MODES and bool(target and mode in target["modes"]);add("mode",mode_ok,policy["description"] if mode_ok else "Невідомий або непідтримуваний режим")
        ready=all(c["ok"] for c in checks);token=self._approval_token(device_id,profile,mode,identity) if ready else "";self._result={"ready":ready,"deviceId":device_id,"profile":profile,"mode":mode,"checks":checks,"reason":"Готово до наступного етапу" if ready else "Destructive flashing заблоковано","artifactSha256":self._artifact["sha256"] if self._artifact["verified"] else "","approvalToken":token};self.changed.emit();return ready
    @Slot(str,str,str,result=bool)
    def approvalMatches(self,device_id,profile,mode):
        if not self._result.get("ready") or not self._result.get("approvalToken") or not self._artifact.get("verified"):return False
        device=next((d for d in self.devices.items if d.get("id")==device_id),None);identity=(device or {}).get("openipcIdentity") or {}
        return self._result.get("deviceId")==device_id and self._result.get("profile")==profile and self._result.get("mode")==mode and self._result.get("approvalToken")==self._approval_token(device_id,profile,mode,identity)
    @Slot()
    def reset(self):self._artifact=self._empty_artifact();self._result=self._empty();self.changed.emit()
