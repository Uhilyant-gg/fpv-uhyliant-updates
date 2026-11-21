"""Safety gates and immutable firmware artifact verification for OpenIPC operations."""
import hashlib
from pathlib import Path
from PySide6.QtCore import QObject,Property,Signal,Slot
from openipc_upgrade import upgrade_candidate
SUPPORTED_PROFILES={"ssc30kq-imx335":{"platform":"ssc30kq","sensor":"imx335","modes":{"primary":{"requiresExistingOpenIPC":False},"upgrade":{"requiresExistingOpenIPC":True},"recovery-fullflash":{"requiresExistingOpenIPC":True}}}}
MODES=("primary","upgrade","recovery-fullflash")
class FirmwareCenter(QObject):
 changed=Signal()
 def __init__(self,devices):super().__init__();self.devices=devices;self._artifact=self._empty_artifact();self._result=self._empty();self._plan=self._empty_plan()
 def _empty(self):return {"ready":False,"deviceId":"","profile":"","mode":"","checks":[],"reason":"Попередню перевірку не виконано","approvalToken":""}
 def _empty_artifact(self):return {"path":"","sha256":"","expectedSha256":"","size":0,"verified":False,"error":"Образ прошивки не вибрано"}
 def _empty_plan(self):return {"ready":False,"steps":[],"reason":"План виконання не підготовлено","approvalToken":""}
 @Property("QVariantMap",notify=changed)
 def result(self):return dict(self._result)
 @Property("QVariantMap",notify=changed)
 def artifact(self):return dict(self._artifact)
 @Property("QVariantMap",notify=changed)
 def executionPlan(self):return dict(self._plan)
 @Property("QStringList",constant=True)
 def profiles(self):return list(SUPPORTED_PROFILES)
 @Property("QStringList",constant=True)
 def modes(self):return list(MODES)
 @Slot(str,result="QVariantMap")
 def upgradeReadiness(self,device_id):return upgrade_candidate(next((d for d in self.devices.items if d.get("id")==device_id),None))
 @Slot(str,result="QVariantMap")
 def modePolicy(self,mode):
  if mode=="primary":return {"title":"Первинне встановлення","requiresExistingOpenIPC":False,"description":"Первинне встановлення. Не використовує recovery/fullflash як універсальний метод."}
  if mode=="upgrade":return {"title":"Оновлення","requiresExistingOpenIPC":True,"description":"Штатне оновлення лише для підтвердженого сумісного OpenIPC."}
  if mode=="recovery-fullflash":return {"title":"Відновлення / fullflash","requiresExistingOpenIPC":True,"description":"Recovery/fullflash лише для пристрою з підтвердженою сумісною кастомною OpenIPC."}
  return {"title":"Невідомий режим","requiresExistingOpenIPC":True,"description":"Невідомий режим заблоковано."}
 def _invalidate(self,reason="Вхідні дані змінилися; повторіть попередню перевірку"):
  self._plan=self._empty_plan()
  if self._result.get("ready") or self._result.get("approvalToken"):self._result={**self._result,"ready":False,"reason":reason,"approvalToken":""}
 @Slot(str,str,result=bool)
 def verifyImage(self,path,expected_sha256):
  self._invalidate();expected=expected_sha256.strip().lower();p=Path(path.strip())
  if not p.is_file():self._artifact={"path":str(p),"sha256":"","expectedSha256":expected,"size":0,"verified":False,"error":"Образ прошивки не знайдено"};self.changed.emit();return False
  h=hashlib.sha256();size=0
  try:
   with p.open("rb") as f:
    for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk);size+=len(chunk)
  except OSError as exc:self._artifact={"path":str(p),"sha256":"","expectedSha256":expected,"size":0,"verified":False,"error":str(exc)};self.changed.emit();return False
  actual=h.hexdigest();valid=len(expected)==64 and all(c in "0123456789abcdef" for c in expected);verified=valid and actual==expected;self._artifact={"path":str(p),"sha256":actual,"expectedSha256":expected,"size":size,"verified":verified,"error":"" if verified else ("Некоректний очікуваний SHA-256" if not valid else "SHA-256 не збігається")};self.changed.emit();return verified
 def _approval_token(self,device_id,profile,mode,identity):
  material="|".join((device_id,profile,mode,self._artifact["sha256"],str(self._artifact["size"]),str(identity.get("platform","")).lower(),str(identity.get("sensor","")).lower(),str(bool(identity.get("verified")))));return hashlib.sha256(material.encode()).hexdigest()
 @Slot(str,str,str,bool,bool,result=bool)
 def precheck(self,device_id,profile,mode,recovery_ready,layout_verified):
  device=next((d for d in self.devices.items if d.get("id")==device_id),None);identity=(device or {}).get("openipcIdentity") or {};target=SUPPORTED_PROFILES.get(profile);checks=[];policy=self.modePolicy(mode)
  def add(name,ok,detail):checks.append({"name":name,"ok":bool(ok),"detail":detail})
  add("device",device is not None,"Пристрій знайдено" if device else "Пристрій не знайдено");add("profile",target is not None,"Профіль прошивки відомий" if target else "Невідомий профіль прошивки");compatible=bool(target and identity.get("platform") and identity.get("sensor") and identity.get("platform","").lower()==target["platform"] and identity.get("sensor","").lower()==target["sensor"]);add("hardware",compatible,"Платформа та сенсор відповідають профілю" if compatible else "Платформа та сенсор не підтверджують сумісність");required=bool(policy.get("requiresExistingOpenIPC",True));openipc_ok=bool(identity.get("verified")) if required else True;add("existing-openipc",openipc_ok,"Наявну OpenIPC підтверджено" if required and openipc_ok else ("Наявна OpenIPC не є вимогою первинного встановлення" if not required else "Наявну OpenIPC не підтверджено"));add("layout",layout_verified,"Розмітку флеш-пам'яті перевірено" if layout_verified else "Розмітку флеш-пам'яті не перевірено");add("image",self._artifact["verified"],"SHA-256 образу прошивки перевірено" if self._artifact["verified"] else (self._artifact["error"] or "Образ прошивки не перевірено"));add("recovery",recovery_ready,"Шлях відновлення готовий" if recovery_ready else "Шлях відновлення не підтверджено");mode_ok=mode in MODES and bool(target and mode in target["modes"]);add("mode",mode_ok,policy["description"] if mode_ok else "Невідомий або непідтримуваний режим")
  ready=all(c["ok"] for c in checks);token=self._approval_token(device_id,profile,mode,identity) if ready else "";self._plan=self._empty_plan();self._result={"ready":ready,"deviceId":device_id,"profile":profile,"mode":mode,"checks":checks,"reason":"Готово до наступного етапу" if ready else "Руйнівне прошивання заблоковано","artifactSha256":self._artifact["sha256"] if self._artifact["verified"] else "","approvalToken":token};self.changed.emit();return ready
 @Slot(str,str,str,result=bool)
 def approvalMatches(self,device_id,profile,mode):
  if not self._result.get("ready") or not self._result.get("approvalToken") or not self._artifact.get("verified"):return False
  device=next((d for d in self.devices.items if d.get("id")==device_id),None);identity=(device or {}).get("openipcIdentity") or {};return self._result.get("deviceId")==device_id and self._result.get("profile")==profile and self._result.get("mode")==mode and self._result.get("approvalToken")==self._approval_token(device_id,profile,mode,identity)
 @Slot(str,str,str,result=bool)
 def prepareExecution(self,device_id,profile,mode):
  if not self.approvalMatches(device_id,profile,mode):self._plan={"ready":False,"steps":[],"reason":"Схвалення попередньої перевірки не відповідає поточним вхідним даним","approvalToken":""};self.changed.emit();return False
  steps=["Повторно перевірити SHA-256 прошивки безпосередньо перед записом","Отримати ексклюзивне блокування операцій із пристроєм"]
  if mode=="primary":steps+=["Запустити адаптер первинного встановлення","Перезапустити пристрій"]
  elif mode=="upgrade":steps+=["Запустити адаптер штатного OpenIPC sysupgrade","Перезапустити пристрій"]
  else:steps+=["Запустити recovery/fullflash адаптер для підтвердженої кастомної OpenIPC","Перезапустити пристрій"]
  steps+=["Повторно виявити пристрій","Перевірити ідентичність OpenIPC і прошивку","Зняти ексклюзивне блокування операцій із пристроєм"]
  self._plan={"ready":True,"steps":steps,"reason":"План підготовлено; апаратний виконавець потребує фізичної перевірки","approvalToken":self._result["approvalToken"]};self.changed.emit();return True
 @Slot()
 def reset(self):self._artifact=self._empty_artifact();self._result=self._empty();self._plan=self._empty_plan();self.changed.emit()
