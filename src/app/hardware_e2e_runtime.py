from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
from hardware_e2e import hardware_e2e_readiness

class HardwareE2ERuntime(QObject):
 changed=Signal()
 def __init__(self,devices,diagnostics,credentials):
  super().__init__();self.devices=devices;self.diagnostics=diagnostics;self.credentials=credentials;self._host_key_accepted=False;self._accepted_identity=None
  for obj in (devices,diagnostics,credentials):
   signal=getattr(obj,'changed',None)
   if signal is not None:signal.connect(self._source_changed)
 def _selected(self):return next((dict(x) for x in getattr(self.devices,'_items',[]) if x.get('active')),next((dict(x) for x in getattr(self.devices,'_items',[])),{}))
 def _network(self):return ((self.diagnostics.build().get('network') or {}).get('evidence') or {})
 def _identity_key(self):
  device=self._selected();identity=dict(device.get('openipcIdentity') or {})
  return (device.get('id') or '',device.get('host') or '',identity.get('platform') or '',identity.get('sensor') or '')
 def _source_changed(self):
  current=self._identity_key()
  if self._host_key_accepted and current!=self._accepted_identity:self._host_key_accepted=False;self._accepted_identity=None
  self.changed.emit()
 @Property('QVariantMap',notify=changed)
 def readiness(self):return hardware_e2e_readiness(self._selected(),self._network(),bool(self.credentials.snapshot().get('hasPassword')),self._host_key_accepted and self._identity_key()==self._accepted_identity)
 @Property(bool,notify=changed)
 def hostKeyAccepted(self):return self._host_key_accepted and self._identity_key()==self._accepted_identity
 @Slot(bool)
 def setHostKeyAccepted(self,value):
  self._host_key_accepted=bool(value);self._accepted_identity=self._identity_key() if self._host_key_accepted else None;self.changed.emit()
 @Slot()
 def reset(self):self._host_key_accepted=False;self._accepted_identity=None;self.changed.emit()
 @Slot(result=str)
 def exportPreflight(self):return self.diagnostics.export()
