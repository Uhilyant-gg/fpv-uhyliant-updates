"""Guarded firmware executor boundary. Destructive hardware work requires an explicit adapter."""
import hashlib
from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
from firmware_center import SUPPORTED_PROFILES
from post_flash_verify import verify_post_flash
class FirmwareExecutor(QObject):
 changed=Signal()
 def __init__(self,firmware_center):super().__init__();self.center=firmware_center;self._adapter=None;self._locked_device='';self._before={};self._handoff={};self._state=self._idle()
 def _idle(self):return {'state':'idle','deviceId':'','profile':'','mode':'','step':'','error':'','verification':{},'hardwareValidation':'hardware-validation-pending'}
 @Property('QVariantMap',notify=changed)
 def status(self):return deepcopy(self._state)
 @Property(bool,notify=changed)
 def busy(self):return bool(self._locked_device)
 def register_adapter(self,adapter):self._adapter=adapter
 def _device(self,did):return next((d for d in self.center.devices.items if d.get('id')==did),None)
 def _set(self,state,**extra):self._state={**self._state,'state':state,**extra};self.changed.emit()
 def _rehash(self):
  a=self.center.artifact
  try:
   h=hashlib.sha256()
   with open(a.get('path',''),'rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
   return bool(a.get('sha256') and h.hexdigest()==a['sha256'])
  except OSError:return False
 def _approved_handoff(self,device_id,profile,mode):
  plan=deepcopy(self.center.executionPlan);artifact=deepcopy(self.center.artifact);approval=deepcopy(self.center.result)
  if not plan.get('ready') or not self.center.approvalMatches(device_id,profile,mode):return None
  if approval.get('deviceId')!=device_id or approval.get('profile')!=profile or approval.get('mode')!=mode:return None
  if plan.get('approvalToken')!=approval.get('approvalToken') or not plan.get('approvalToken'):return None
  if not self._rehash():return None
  return {'deviceId':device_id,'profile':profile,'mode':mode,'artifact':artifact,'plan':plan,'approval':approval}
 @Slot(str,str,str,result=bool)
 def execute(self,device_id,profile,mode):
  if self._locked_device:self._set('blocked',error='Інша firmware operation вже активна');return False
  handoff=self._approved_handoff(device_id,profile,mode)
  if handoff is None:self._set('blocked',error='Execution plan, immutable approval або firmware SHA-256 невалідні');return False
  device=self._device(device_id)
  if not device:self._set('blocked',error='Approved device більше не існує');return False
  identity=dict(device.get('openipcIdentity') or {});self._before=identity
  if identity.get('verified') is not True:self._set('blocked',error='Verified OpenIPC identity втрачено перед execution');return False
  expected=SUPPORTED_PROFILES.get(profile,{})
  if identity.get('platform','').lower()!=str(expected.get('platform','')).lower() or identity.get('sensor','').lower()!=str(expected.get('sensor','')).lower():self._set('blocked',error='Hardware identity змінилася після approval');return False
  if self._adapter is None:self._set('hardware-validation-pending',deviceId=device_id,profile=profile,mode=mode,step='executor',error='Hardware executor adapter не підключений');return False
  self._handoff=handoff;self._locked_device=device_id;self._set('executing',deviceId=device_id,profile=profile,mode=mode,step='flash',error='',verification={})
  try:
   ok=bool(self._adapter.execute(device_id,profile,mode,deepcopy(handoff['artifact']),deepcopy(handoff['plan'])));self._set('reboot-pending' if ok else 'error',step='rediscover' if ok else 'flash',error='' if ok else 'Executor повідомив про помилку');return ok
  except Exception as exc:self._set('error',step='flash',error=str(exc));return False
  finally:self._locked_device='';self.changed.emit()
 @Slot('QVariantMap',str,result=bool)
 def verifyObserved(self,observed,expected_firmware=''):
  if self._state.get('state')!='reboot-pending' or not self._handoff:return False
  profile=SUPPORTED_PROFILES.get(self._handoff.get('profile'),{});result=verify_post_flash(self._before,dict(observed or {}),profile,expected_firmware);self._set('verified' if result['ok'] else 'error',step='verify',verification=result,error='' if result['ok'] else 'Post-operation verification failed');return bool(result['ok'])
 @Slot(bool,bool,result=bool)
 def completeVerification(self,rediscovered,identity_verified):
  if self._state.get('state')!='reboot-pending':return False
  ok=bool(rediscovered and identity_verified);self._set('verified' if ok else 'error',step='verify',error='' if ok else 'Post-operation verification failed');return ok
 @Slot()
 def reset(self):
  if not self._locked_device:self._before={};self._handoff={};self._state=self._idle();self.changed.emit()
