"""Guarded firmware executor boundary. Destructive hardware work requires an explicit adapter."""
import hashlib
from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
from firmware_center import SUPPORTED_PROFILES
class FirmwareExecutor(QObject):
 changed=Signal()
 def __init__(self,firmware_center):super().__init__();self.center=firmware_center;self._adapter=None;self._locked_device='';self._before={};self._handoff={};self._verification_nonce=None;self._state=self._idle()
 def _idle(self):return {'state':'idle','deviceId':'','profile':'','mode':'','step':'','error':'','verification':{},'hardwareValidation':'hardware-validation-pending'}
 @Property('QVariantMap',notify=changed)
 def status(self):return deepcopy(self._state)
 @Property(bool,notify=changed)
 def busy(self):return bool(self._locked_device)
 def register_adapter(self,adapter):
  if self._locked_device:return False
  self._adapter=adapter;return True
 def _device(self,did):return next((d for d in self.center.devices.items if d.get('id')==did),None)
 def _set(self,state,**extra):self._state={**self._state,'state':state,**extra};self.changed.emit()
 def _release_lock(self):self._locked_device='';self._verification_nonce=None;self.changed.emit()
 def _rehash(self,artifact):
  try:
   h=hashlib.sha256();size=0
   with open(artifact.get('path',''),'rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);size+=len(chunk)
   return bool(artifact.get('sha256') and h.hexdigest()==artifact['sha256'] and size==artifact.get('size'))
  except OSError:return False
 def _approved_handoff(self,device_id,profile,mode):
  plan=deepcopy(self.center.executionPlan);artifact=deepcopy(self.center.artifact);approval=deepcopy(self.center.result)
  if not plan.get('ready') or not self.center.approvalMatches(device_id,profile,mode):return None
  if approval.get('deviceId')!=device_id or approval.get('profile')!=profile or approval.get('mode')!=mode:return None
  if plan.get('approvalToken')!=approval.get('approvalToken') or not plan.get('approvalToken'):return None
  if plan.get('artifactSha256')!=artifact.get('sha256') or plan.get('artifactSize')!=artifact.get('size') or approval.get('artifactSha256')!=artifact.get('sha256'):return None
  if not self._rehash(artifact):return None
  return {'deviceId':device_id,'profile':profile,'mode':mode,'artifact':artifact,'plan':plan,'approval':approval}
 @Slot(str,str,str,result=bool)
 def execute(self,device_id,profile,mode):
  if self._locked_device:self._set('blocked',error='Інша операція з прошивкою вже активна');return False
  handoff=self._approved_handoff(device_id,profile,mode)
  if handoff is None:self._set('blocked',error='План виконання, незмінне схвалення або SHA-256/розмір прошивки невалідні');return False
  device=self._device(device_id)
  if not device:self._set('blocked',error='Схвалений пристрій більше не існує');return False
  identity=dict(device.get('openipcIdentity') or {});self._before=identity
  if identity.get('verified') is not True:self._set('blocked',error='Підтверджену ідентичність OpenIPC втрачено перед виконанням');return False
  expected=SUPPORTED_PROFILES.get(profile,{})
  if identity.get('platform','').lower()!=str(expected.get('platform','')).lower() or identity.get('sensor','').lower()!=str(expected.get('sensor','')).lower():self._set('blocked',error='Апаратна ідентичність змінилася після схвалення');return False
  if self._adapter is None:self._set('hardware-validation-pending',deviceId=device_id,profile=profile,mode=mode,step='executor',error='Апаратний адаптер виконавця не підключений');return False
  handoff['host']=str(device.get('host','')).strip();handoff['platform']=str(identity.get('platform','')).strip().lower();handoff['sensor']=str(identity.get('sensor','')).strip().lower();handoff['verifiedOpenIPC']=True
  self._handoff=deepcopy(handoff);self._locked_device=device_id;self._set('executing',deviceId=device_id,profile=profile,mode=mode,step='flash',error='',verification={})
  try:
   ok=bool(self._adapter.execute(device_id,profile,mode,deepcopy(handoff['artifact']),deepcopy(handoff['plan']),deepcopy(handoff)))
  except Exception:
   self._set('error',step='flash',error='Виконавець повідомив про помилку');self._release_lock();return False
  if not ok:self._set('error',step='flash',error='Виконавець повідомив про помилку');self._release_lock();return False
  self._set('reboot-pending',step='rediscover',error='');return True
 def verificationContext(self):
  if self._state.get('state')!='reboot-pending' or not self._handoff:return {'ready':False}
  host=str(self._handoff.get('host','')).strip()
  return {'ready':bool(host),'host':host,'profile':self._handoff.get('profile',''),'before':deepcopy(self._before)}
 def beginRediscovery(self):
  if not self._locked_device or self._state.get('state')!='reboot-pending' or not self._handoff:return None
  context=self.verificationContext()
  if not context.get('ready'):return None
  self._verification_nonce=object();self._set('rediscovering',step='rediscover',error='');return context,self._verification_nonce
 def failRediscovery(self,nonce=None):
  if not self._locked_device or self._state.get('state') not in ('reboot-pending','rediscovering'):return False
  if self._state.get('state')=='rediscovering' and nonce is not self._verification_nonce:return False
  self._set('error',step='rediscover',error='Підтверджену OpenIPC не виявлено після перезапуску',verification={});self._release_lock();return False
 def acceptRediscoveredVerification(self,rediscovery,verification,nonce=None):
  if not self._locked_device or self._state.get('state')!='rediscovering' or nonce is not self._verification_nonce or not isinstance(rediscovery,dict) or rediscovery.get('rediscovered') is not True or not isinstance(verification,dict):return False
  result=deepcopy(verification);result['rediscoveryAttempts']=rediscovery.get('attempts',0)
  ok=result.get('ok') is True;self._set('verified' if ok else 'error',step='verify',verification=result,error='' if ok else 'Перевірка після операції не пройдена');self._release_lock();return ok
 @Slot()
 def reset(self):
  if self._locked_device:return False
  self._before={};self._handoff={};self._verification_nonce=None;self._state=self._idle();self.changed.emit();return True
