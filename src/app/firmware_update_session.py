"""Safe orchestration boundary for a complete OpenIPC update session."""
from copy import deepcopy
import ipaddress,threading
from PySide6.QtCore import QObject,Property,Signal,Slot
from firmware_update_lifecycle import FirmwareUpdateLifecycle
from firmware_rediscovery import FirmwareRediscovery
from openipc_upgrade_transport import OpenIPCUpgradeAdapter
from route_discovery import fingerprint

class FirmwareUpdateSession(QObject):
 changed=Signal()
 def __init__(self,executor,devices):
  super().__init__();self.executor=executor;self.devices=devices;self._enabled=False;self._result=self._empty()
 def _empty(self):return {'enabled':False,'state':'hardware-validation-pending','reason':'Апаратний транспорт оновлення не підключено','observedFirmware':'','verification':{}}
 @Property('QVariantMap',notify=changed)
 def result(self):return deepcopy(self._result)
 def configure_transport(self,transport):
  if self.executor.busy:return False
  self._enabled=transport is not None
  self.executor.register_adapter(OpenIPCUpgradeAdapter(self.devices,transport) if transport is not None else None)
  self._result={'enabled':True,'state':'ready','reason':'Транспорт підключено для явної апаратної перевірки','observedFirmware':'','verification':{}} if self._enabled else self._empty();self.changed.emit();return True
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
  context=self.executor.verificationContext()
  if not context.get('ready'):return self._sync(False)
  try:address=ipaddress.ip_address(context.get('host',''))
  except ValueError:return self._sync(self.executor.failRediscovery())
  if address.version!=4 or address.is_unspecified or address.is_loopback or address.is_multicast:return self._sync(self.executor.failRediscovery())
  lifecycle=FirmwareUpdateLifecycle(self.executor,FirmwareRediscovery(self._probe));ok=lifecycle.verify_after_reboot();return self._sync(ok)
 @Slot()
 def reset(self):
  if self.executor.busy:return False
  self.executor.reset();self._result={'enabled':self._enabled,'state':'ready' if self._enabled else 'hardware-validation-pending','reason':'' if self._enabled else 'Апаратний транспорт оновлення не підключено','observedFirmware':'','verification':{}};self.changed.emit();return True
