"""Safe orchestration boundary for a complete OpenIPC update session.

The destructive adapter remains opt-in. This object never owns or exposes plaintext
credentials; authentication stays inside the injected transport.
"""
from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
from firmware_update_lifecycle import FirmwareUpdateLifecycle
from firmware_rediscovery import FirmwareRediscovery
from openipc_upgrade_transport import OpenIPCUpgradeAdapter
from route_discovery import fingerprint
import threading

class FirmwareUpdateSession(QObject):
 changed=Signal()
 def __init__(self,executor,devices):
  super().__init__();self.executor=executor;self.devices=devices;self._transport=None;self._enabled=False;self._result=self._empty()
 def _empty(self):return {'enabled':False,'state':'hardware-validation-pending','reason':'Апаратний транспорт оновлення не підключено','observedFirmware':'','verification':{}}
 @Property('QVariantMap',notify=changed)
 def result(self):return deepcopy(self._result)
 def configure_transport(self,transport):
  self._transport=transport;self._enabled=transport is not None
  if self._enabled:self.executor.register_adapter(OpenIPCUpgradeAdapter(self.devices,transport));self._result={'enabled':True,'state':'ready','reason':'Транспорт підключено для явної апаратної перевірки','observedFirmware':'','verification':{}}
  else:self.executor.register_adapter(None);self._result=self._empty()
  self.changed.emit()
 def _probe(self,host):return fingerprint(host,threading.Event())
 def _sync(self,ok=None):
  status=self.executor.status;verification=status.get('verification') or {};identity=verification.get('identity') or {}
  self._result={'enabled':self._enabled,'state':status.get('state',''),'reason':status.get('error',''),'observedFirmware':identity.get('firmware',''),'verification':verification};self.changed.emit();return bool(ok) if ok is not None else True
 @Slot(str,str,str,result=bool)
 def execute(self,device_id,profile,mode):
  if not self._enabled:self._result=self._empty();self.changed.emit();return False
  return self._sync(self.executor.execute(device_id,profile,mode))
 @Slot(result=bool)
 def verifyAfterReboot(self):
  if not self._enabled:return False
  lifecycle=FirmwareUpdateLifecycle(self.executor,FirmwareRediscovery(self._probe));return self._sync(lifecycle.verify_after_reboot())
 @Slot()
 def reset(self):self.executor.reset();self._result={'enabled':self._enabled,'state':'ready' if self._enabled else 'hardware-validation-pending','reason':'' if self._enabled else 'Апаратний транспорт оновлення не підключено','observedFirmware':'','verification':{}};self.changed.emit()
