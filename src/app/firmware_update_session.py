"""Safe orchestration boundary for a complete OpenIPC update session."""
from copy import deepcopy
import threading,time,uuid
from PySide6.QtCore import QObject,Property,Signal,Slot
from devices import interfaces
from firmware_update_lifecycle import FirmwareUpdateLifecycle
from firmware_rediscovery import FirmwareRediscovery,_private_candidate
from openipc_upgrade_transport import OpenIPCUpgradeAdapter
from authenticated_camera_transport import AuthenticatedCameraTransport
from route_discovery import fingerprint,plan_targets,system_routes

class FirmwareUpdateSession(QObject):
 changed=Signal()
 def __init__(self,executor,devices,probe=None,candidates=None,sleep=time.sleep,rediscovery_attempts=30,rediscovery_interval=2.0,events=None):
  super().__init__();self.executor=executor;self.devices=devices;self._enabled=False;self._result=self._empty();self._probe_provider=probe;self._candidate_provider=candidates;self._sleep=sleep;self._rediscovery_attempts=max(1,min(int(rediscovery_attempts),120));self._rediscovery_interval=max(0.0,min(float(rediscovery_interval),10.0));self._events=events;self._correlation_id=''
 def _empty(self):return {'enabled':False,'state':'hardware-validation-pending','reason':'Апаратний транспорт оновлення не підключено','observedFirmware':'','verification':{}}
 def _event(self,level,message,detail=None):
  if self._events is None:return
  try:self._events.record('firmware',level,message,self._correlation_id or None,detail)
  except Exception:pass
 @Property('QVariantMap',notify=changed)
 def result(self):return deepcopy(self._result)
 def configure_transport(self,transport):
  if self.executor.busy:return False
  self._enabled=transport is not None
  self.executor.register_adapter(OpenIPCUpgradeAdapter(self.devices,transport) if transport is not None else None)
  self._result={'enabled':True,'state':'ready','reason':'Транспорт підключено для явної апаратної перевірки','observedFirmware':'','verification':{}} if self._enabled else self._empty();self.changed.emit();return True
 @Slot(QObject,QObject,result=bool)
 def enableAuthenticatedTransport(self,credentials,preflight=None):
  if self.executor.busy or credentials is None or preflight is None:return False
  try:readiness=preflight.readiness;snapshot=credentials.snapshot()
  except Exception:return False
  if not isinstance(readiness,dict) or readiness.get('ready') is not True:return False
  if not isinstance(snapshot,dict) or not str(snapshot.get('username','')).strip() or snapshot.get('hasPassword') is not True:return False
  expected=(readiness.get('host'),readiness.get('platform'),readiness.get('sensor'))
  if not _private_candidate(expected[0]) or not str(expected[1] or '').strip() or not str(expected[2] or '').strip():return False
  device=next((dict(d) for d in self.devices.items if d.get('active')),None)
  if device is None:return False
  identity=dict(device.get('openipcIdentity') or {})
  current=(device.get('host'),identity.get('platform'),identity.get('sensor'))
  if current!=expected or identity.get('verified') is not True:return False
  ok=self.configure_transport(AuthenticatedCameraTransport(credentials))
  if ok:self._event('info','authenticated transport ready',{'deviceId':device.get('id'),'host':current[0],'platform':current[1],'sensor':current[2]})
  return ok
 @Slot(result=bool)
 def disableTransport(self):return self.configure_transport(None)
 def _probe(self,host):
  if callable(self._probe_provider):return self._probe_provider(host)
  return fingerprint(host,threading.Event())
 def _rediscovery_candidates(self,original_host):
  if callable(self._candidate_provider):return self._candidate_provider(original_host)
  return plan_targets(interfaces(),system_routes(),[original_host])
 def _sync(self,ok=None):
  status=self.executor.status;verification=status.get('verification') or {};identity=verification.get('identity') or {}
  self._result={'enabled':self._enabled,'state':status.get('state',''),'reason':status.get('error',''),'observedFirmware':identity.get('firmware',''),'verification':verification};self.changed.emit();return bool(ok) if ok is not None else True
 @Slot(str,str,str,result=bool)
 def execute(self,device_id,profile,mode):
  if not self._enabled:self._result=self._empty();self.changed.emit();return False
  self._correlation_id=uuid.uuid4().hex;self._event('info','firmware update requested',{'deviceId':device_id,'profile':profile,'mode':mode})
  ok=self.executor.execute(device_id,profile,mode);self._sync(ok);state=self._result.get('state','')
  self._event('info' if ok else 'error','firmware dispatch accepted' if ok else 'firmware dispatch blocked',{'deviceId':device_id,'profile':profile,'mode':mode,'state':state,'reason':self._result.get('reason','')})
  return bool(ok)
 @Slot(result=bool)
 def verifyAfterReboot(self):
  if not self._enabled:return False
  context=self.executor.verificationContext()
  if not context.get('ready'):self._event('error','post-update verification unavailable',{'state':self.executor.status.get('state','')});return self._sync(False)
  detail={'host':context.get('host',''),'profile':context.get('profile',''),'expectedFirmware':context.get('expectedFirmware','')};self._event('info','post-update rediscovery started',detail)
  if not _private_candidate(context.get('host','')):return self._verification_failed(detail,self.executor.failRediscovery())
  before=context.get('before') or {}
  if not str(before.get('platform','')).strip() or not str(before.get('sensor','')).strip():return self._verification_failed(detail,self.executor.failRediscovery())
  rediscovery=FirmwareRediscovery(self._probe,sleep=self._sleep,candidates=self._rediscovery_candidates);lifecycle=FirmwareUpdateLifecycle(self.executor,rediscovery)
  ok=lifecycle.verify_after_reboot(self._rediscovery_attempts,self._rediscovery_interval);self._sync(ok);verification=self._result.get('verification') or {};identity=verification.get('identity') or {};detail.update({'state':self._result.get('state',''),'rediscoveredHost':verification.get('rediscoveredHost',''),'observedFirmware':identity.get('firmware','')});self._event('info' if ok else 'error','post-update verification passed' if ok else 'post-update verification failed',detail);return bool(ok)
 def _verification_failed(self,detail,ok):
  self._sync(ok);detail=dict(detail);detail['state']=self._result.get('state','');self._event('error','post-update verification failed',detail);return False
 @Slot()
 def reset(self):
  if self.executor.busy:return False
  self.executor.reset();self._result={'enabled':self._enabled,'state':'ready' if self._enabled else 'hardware-validation-pending','reason':'' if self._enabled else 'Апаратний транспорт оновлення не підключено','observedFirmware':'','verification':{}};self._correlation_id='';self.changed.emit();return True
