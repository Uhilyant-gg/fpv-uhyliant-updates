"""Read-only external-navigation and network-link observations. No control output is produced."""
import math,time
from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
class LinkDiagnostics(QObject):
 changed=Signal()
 def __init__(self,clock=None,stale_after=5.0):
  super().__init__();self._clock=clock or time.monotonic
  try:self._stale_after=float(stale_after)
  except (TypeError,ValueError):self._stale_after=5.0
  if not math.isfinite(self._stale_after) or self._stale_after<=0:self._stale_after=5.0
  self._external=self._empty_external();self._network=self._empty_network()
 def _empty_external(self):return {'available':False,'source':None,'state':'unavailable','quality':None,'detail':None,'observedAt':None}
 def _empty_network(self):return {'available':False,'transport':None,'state':'unavailable','interface':None,'endpoint':None,'rttMs':None,'detail':None,'observedAt':None}
 def _public(self,item):
  out=deepcopy(item);at=out.get('observedAt')
  if at is not None and self._clock()-at>self._stale_after:out['state']='stale';out['available']=False
  return out
 @Property('QVariantMap',notify=changed)
 def externalNavigation(self):return self._public(self._external)
 @Property('QVariantMap',notify=changed)
 def network(self):return self._public(self._network)
 @Property('QVariantMap',notify=changed)
 def snapshot(self):return {'externalNavigation':self.externalNavigation,'network':self.network}
 @Slot(str,str,str,str)
 def observeExternalNavigation(self,source,state,quality,detail):
  source=(source or '').strip();state=(state or '').strip().lower();quality=(quality or '').strip() or None;detail=(detail or '').strip() or None;valid=bool(source and state in ('ready','degraded','error'));self._external={'available':valid,'source':source or None,'state':state if valid else 'unavailable','quality':quality if valid else None,'detail':detail if valid else None,'observedAt':self._clock() if valid else None};self.changed.emit()
 @Slot(str,str,str,str,'QVariant',str)
 def observeNetwork(self,transport,state,interface,endpoint,rtt_ms,detail):
  transport=(transport or '').strip();state=(state or '').strip().lower();interface=(interface or '').strip() or None;endpoint=(endpoint or '').strip() or None;detail=(detail or '').strip() or None
  try:rtt=float(rtt_ms)
  except (TypeError,ValueError):rtt=None
  if rtt is not None and (not math.isfinite(rtt) or rtt<0):rtt=None
  valid=bool(transport and state in ('ready','degraded','error'))
  self._network={'available':valid,'transport':transport or None,'state':state if valid else 'unavailable','interface':interface if valid else None,'endpoint':endpoint if valid else None,'rttMs':rtt if valid else None,'detail':detail if valid else None,'observedAt':self._clock() if valid else None};self.changed.emit()
 @Slot()
 def clearExternalNavigation(self):self._external=self._empty_external();self.changed.emit()
 @Slot()
 def clearNetwork(self):self._network=self._empty_network();self.changed.emit()
 @Slot()
 def clear(self):self._external=self._empty_external();self._network=self._empty_network();self.changed.emit()
