from copy import deepcopy
from pathlib import Path
import time
from PySide6.QtCore import QObject,Property,Signal,Slot
from diagnostics_bundle import diagnostic_bundle,export_bundle
from network_remediation import classify_network,remediation
from network_evidence import collect_network_evidence
from devices import interfaces
from route_discovery import system_routes
class DiagnosticsRuntime(QObject):
 changed=Signal()
 def __init__(self,version,devices,links,telemetry,updater,events,data_dir,video=None):super().__init__();self.version=version;self.devices=devices;self.links=links;self.telemetry=telemetry;self.updater=updater;self.events=events;self.data_dir=Path(data_dir);self.video=video;self._last_remediation={};self._correlation_id=None;self._export_sequence=0
 def _devices(self):return deepcopy(getattr(self.devices,'_items',[]) or [])
 def _video(self):
  v=self.video
  if v is None:return {}
  return {'primary':{'state':getattr(getattr(v,'primary',None),'state',None)},'secondary':{'state':getattr(getattr(v,'secondary',None),'state',None)}}
 def _network_evidence(self,devices):
  discovered=list(getattr(self.devices,'_discovered',[]) or []);manual=getattr(self.devices,'_manual_result',{}) or {}
  if isinstance(manual,dict) and manual:discovered.append(manual)
  return collect_network_evidence(interfaces(),system_routes(),devices,discovered)
 def _network_health(self,network,video,devices,evidence):
  finding=classify_network(network,(video.get('primary') or {}).get('state'),bool(devices));finding['remediation']=remediation(finding.get('action'));finding['evidenceSummary']=deepcopy(evidence.get('summary',{}));return finding
 def build(self):
  devices=self._devices();network=dict(self.links.snapshot);video=self._video();evidence=self._network_evidence(devices);network['evidence']=evidence;bundle=diagnostic_bundle(self.version,devices=devices,network=network,video=video,protocols={'active':self.telemetry.name,'available':self.telemetry.available,'error':self.telemetry.error,'telemetry':dict(self.telemetry.telemetry)},updater={'state':self.updater.updateState,'status':self.updater.updateStatus,'availableVersion':self.updater.availableVersion,'progress':self.updater.progress},events=self.events.snapshot(),correlation_id=self._correlation_id);self._correlation_id=bundle['correlationId'];bundle['networkHealth']=self._network_health(network,video,devices,evidence);bundle['lastRemediation']=deepcopy(self._last_remediation);return bundle
 def _run_safe(self,action):
  if action=='rediscover' and hasattr(self.devices,'discoverOpenIPC'):self.devices.discoverOpenIPC();return True
  if action=='reconnect-video' and self.video is not None:
   primary=getattr(self.video,'primary',None);return bool(primary and hasattr(primary,'reconnect') and primary.reconnect())
  if action=='refresh-network':self.links.changed.emit();return True
  return False
 def _export_path(self,label=None):
  safe=''.join(c if c.isalnum() or c in ('-','_') else '-' for c in str(label or '').strip().lower()).strip('-_') or 'snapshot';self._export_sequence+=1;stamp=int(time.time());return self.data_dir/'diagnostics'/f'diagnostic-{stamp}-{self._export_sequence:03d}-{safe}.json'
 @Property('QVariantMap',notify=changed)
 def snapshot(self):return self.build()
 @Slot(str,result=bool)
 def applyRemediation(self,action):
  allowed=remediation(action)
  if not allowed or allowed.get('mutating'):return False
  before=self.build().get('networkHealth',{});ok=self._run_safe(action);after=self.build().get('networkHealth',{});self._last_remediation={'action':action,'ok':bool(ok),'before':before.get('state'),'after':after.get('state')};self.events.record('diagnostics','info' if ok else 'warning','safe remediation executed',detail=deepcopy(self._last_remediation));self.changed.emit();return bool(ok)
 @Slot(result=str)
 def export(self):return self.exportStage('snapshot')
 @Slot(str,result=str)
 def exportStage(self,label):
  path=self._export_path(label);bundle=self.build();bundle['capture']={'label':str(label or '').strip() or 'snapshot','sequence':self._export_sequence};export_bundle(path,bundle);self.events.record('diagnostics','info','diagnostic bundle exported',correlation_id=bundle.get('correlationId'),detail={'file':path.name,'label':bundle['capture']['label'],'sequence':self._export_sequence});self.changed.emit();return str(path)
