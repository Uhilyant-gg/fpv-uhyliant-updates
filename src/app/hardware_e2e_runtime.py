from copy import deepcopy
from PySide6.QtCore import QObject,Property,Signal,Slot
from hardware_e2e import hardware_e2e_readiness
class HardwareE2ERuntime(QObject):
 changed=Signal()
 def __init__(self,devices,diagnostics,credentials,firmware=None,session=None):
  super().__init__();self.devices=devices;self.diagnostics=diagnostics;self.credentials=credentials;self.firmware=firmware;self.session=session;self._host_key_accepted=False;self._accepted_identity=None;self._selected_device_id='';self._captures={};self._evidence_binding=None
  for obj in (devices,diagnostics,credentials,firmware,session):
   signal=getattr(obj,'changed',None) if obj is not None else None
   if signal is not None:signal.connect(self._source_changed)
 def _selected(self):
  items=getattr(self.devices,'_items',getattr(self.devices,'items',[]))
  if self._selected_device_id:return next((dict(x) for x in items if x.get('id')==self._selected_device_id),{})
  return next((dict(x) for x in items if x.get('active')),next((dict(x) for x in items),{}))
 def _network(self):return ((self.diagnostics.build().get('network') or {}).get('evidence') or {})
 def _firmware(self):return {'artifact':dict(getattr(self.firmware,'artifact',{}) or {}),'plan':dict(getattr(self.firmware,'executionPlan',{}) or {}),'approval':dict(getattr(self.firmware,'result',{}) or {})} if self.firmware is not None else {}
 def _session_result(self):return dict(getattr(self.session,'result',{}) or {}) if self.session is not None else {}
 def _identity_key(self):
  device=self._selected();identity=dict(device.get('openipcIdentity') or {});fw=self._firmware();artifact=fw.get('artifact') or {};plan=fw.get('plan') or {};approval=fw.get('approval') or {}
  return (device.get('id') or '',device.get('host') or '',identity.get('platform') or '',identity.get('sensor') or '',artifact.get('sha256') or '',artifact.get('size') or 0,plan.get('approvalToken') or '',approval.get('approvalToken') or '')
 def _source_changed(self):
  current=self._identity_key()
  if self._host_key_accepted and current!=self._accepted_identity:self._host_key_accepted=False;self._accepted_identity=None
  if self._evidence_binding is not None and current!=self._evidence_binding:self._captures={};self._evidence_binding=None
  self.changed.emit()
 @Property('QVariantMap',notify=changed)
 def readiness(self):return hardware_e2e_readiness(self._selected(),self._network(),bool(self.credentials.snapshot().get('hasPassword')),self._host_key_accepted and self._identity_key()==self._accepted_identity,self._firmware())
 @Property(bool,notify=changed)
 def hostKeyAccepted(self):return self._host_key_accepted and self._identity_key()==self._accepted_identity
 @Property('QVariantMap',notify=changed)
 def captures(self):return deepcopy(self._captures)
 @Property('QVariantMap',notify=changed)
 def evidenceReadiness(self):
  result=self._session_result();state=str(result.get('state') or '');verification=result.get('verification') or {};identity=verification.get('identity') or {};observed=str(identity.get('firmware') or result.get('observedFirmware') or '').strip();bound=self._evidence_binding is not None and self._identity_key()==self._evidence_binding
  return {'preflight':self.readiness.get('ready') is True,'postUpdate':bound and 'preflight' in self._captures and state=='verified' and verification.get('ok') is True and bool(observed),'failure':bound and 'preflight' in self._captures and state in ('error','blocked'),'state':state,'observedFirmware':observed}
 @Slot(str)
 def selectDevice(self,device_id):
  device_id=str(device_id or '')
  if device_id==self._selected_device_id:return
  self._selected_device_id=device_id;self._host_key_accepted=False;self._accepted_identity=None;self._captures={};self._evidence_binding=None;self.changed.emit()
 @Slot(bool)
 def setHostKeyAccepted(self,value):self._host_key_accepted=bool(value);self._accepted_identity=self._identity_key() if self._host_key_accepted else None;self.changed.emit()
 @Slot()
 def reset(self):self._host_key_accepted=False;self._accepted_identity=None;self._selected_device_id='';self._captures={};self._evidence_binding=None;self.changed.emit()
 @Slot(result=str)
 def exportPreflight(self):return self.capture('preflight')
 @Slot(str,result=str)
 def capture(self,stage):
  stage=str(stage or '').strip().lower();allowed=self.evidenceReadiness
  if stage=='preflight' and not allowed.get('preflight'):return ''
  if stage=='post-update' and not allowed.get('postUpdate'):return ''
  if stage=='failure' and not allowed.get('failure'):return ''
  if stage not in ('preflight','post-update','failure'):return ''
  path=self.diagnostics.exportStage('hardware-e2e-'+stage)
  if stage=='preflight':self._evidence_binding=self._identity_key();self._captures={}
  self._captures[stage]=path;self.changed.emit();return path
