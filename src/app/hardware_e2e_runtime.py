from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
from hardware_e2e import hardware_e2e_readiness

class HardwareE2ERuntime(QObject):
 changed=Signal()
 def __init__(self,devices,diagnostics,credentials):
  super().__init__();self.devices=devices;self.diagnostics=diagnostics;self.credentials=credentials;self._host_key_accepted=False
  for obj in (devices,diagnostics,credentials):
   signal=getattr(obj,'changed',None)
   if signal is not None:signal.connect(self.changed)
 def _selected(self):return next((dict(x) for x in getattr(self.devices,'_items',[]) if x.get('active')),next((dict(x) for x in getattr(self.devices,'_items',[])),{}))
 def _network(self):return ((self.diagnostics.build().get('network') or {}).get('evidence') or {})
 @Property('QVariantMap',notify=changed)
 def readiness(self):return hardware_e2e_readiness(self._selected(),self._network(),bool(self.credentials.snapshot().get('hasPassword')),self._host_key_accepted)
 @Property(bool,notify=changed)
 def hostKeyAccepted(self):return self._host_key_accepted
 @Slot(bool)
 def setHostKeyAccepted(self,value):self._host_key_accepted=bool(value);self.changed.emit()
 @Slot()
 def reset(self):self._host_key_accepted=False;self.changed.emit()
 @Slot(result=str)
 def exportPreflight(self):return self.diagnostics.export()
