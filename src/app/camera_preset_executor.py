"""Guarded camera-preset executor. Presets never carry firmware or video-profile changes."""
from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
from camera_presets import PRESETS,compatible
class CameraPresetExecutor(QObject):
 changed=Signal()
 def __init__(self,presets):super().__init__();self.presets=presets;self._adapter=None;self._locked_device='';self._state=self._idle()
 def _idle(self):return {'state':'idle','deviceId':'','presetId':'','presetVersion':0,'step':'','error':'','hardwareValidation':'hardware-validation-pending'}
 @Property('QVariantMap',notify=changed)
 def status(self):return deepcopy(self._state)
 @Property(bool,notify=changed)
 def busy(self):return bool(self._locked_device)
 def register_adapter(self,adapter):self._adapter=adapter
 def _set(self,state,**extra):self._state={**self._state,'state':state,**extra};self.changed.emit()
 def _device(self,did):return next((d for d in self.presets.devices.items if d.get('id')==did),None)
 def _validate_plan(self):
  plan=deepcopy(self.presets.result.get('plan') or {})
  if not self.presets.result.get('ready') or not plan:return None
  if plan.get('execution')!='hardware-validation-pending' or plan.get('appliesVideoProfile') is not False:return None
  allowed={'role','orientation'};settings=plan.get('settings')
  if not isinstance(settings,dict) or not settings or set(settings)-allowed:return None
  preset=next((p for p in PRESETS.values() if p.get('id')==plan.get('presetId') and p.get('version')==plan.get('presetVersion')),None)
  device=self._device(plan.get('deviceId',''));identity=(device or {}).get('openipcIdentity') or {}
  if not device or not compatible(preset,identity):return None
  if plan.get('platform')!=preset.get('platform') or plan.get('sensor')!=preset.get('sensor') or settings!=preset.get('settings'):return None
  return plan
 @Slot(result=bool)
 def executePrepared(self):
  if self._locked_device:self._set('blocked',error='Інша preset operation вже активна');return False
  plan=self._validate_plan()
  if plan is None:self._set('blocked',error='Camera preset plan або verified hardware identity невалідні');return False
  if self._adapter is None:self._set('hardware-validation-pending',deviceId=plan['deviceId'],presetId=plan['presetId'],presetVersion=plan['presetVersion'],step='executor',error='Camera preset hardware adapter не підключений');return False
  self._locked_device=plan['deviceId'];self._set('executing',deviceId=plan['deviceId'],presetId=plan['presetId'],presetVersion=plan['presetVersion'],step='apply',error='')
  try:
   ok=bool(self._adapter.execute(plan['deviceId'],deepcopy(plan)));self._set('applied-pending-verification' if ok else 'error',step='verify' if ok else 'apply',error='' if ok else 'Preset executor повідомив про помилку');return ok
  except Exception as exc:self._set('error',step='apply',error=str(exc));return False
  finally:self._locked_device='';self.changed.emit()
 @Slot(bool,result=bool)
 def verifyObserved(self,identity_verified):
  if self._state.get('state')!='applied-pending-verification':return False
  device=self._device(self._state.get('deviceId',''));ok=bool(identity_verified and device and (device.get('openipcIdentity') or {}).get('verified') is True);self._set('verified' if ok else 'error',step='verify',error='' if ok else 'Post-preset verified hardware observation unavailable');return ok
 @Slot()
 def reset(self):
  if not self._locked_device:self._state=self._idle();self.changed.emit()
