from copy import deepcopy
from pathlib import Path
from PySide6.QtCore import QObject,Property,Signal,Slot
from diagnostics_bundle import diagnostic_bundle,export_bundle
from network_remediation import classify_network,remediation
class DiagnosticsRuntime(QObject):
 changed=Signal()
 def __init__(self,version,devices,links,telemetry,updater,events,data_dir,video=None):super().__init__();self.version=version;self.devices=devices;self.links=links;self.telemetry=telemetry;self.updater=updater;self.events=events;self.data_dir=Path(data_dir);self.video=video
 def _devices(self):return deepcopy(getattr(self.devices,'_items',[]) or [])
 def _video(self):
  v=self.video
  if v is None:return {}
  return {'primary':{'state':getattr(getattr(v,'primary',None),'state',None)},'secondary':{'state':getattr(getattr(v,'secondary',None),'state',None)}}
 def _network_health(self,network,video,devices):
  finding=classify_network(network,(video.get('primary') or {}).get('state'),bool(devices));finding['remediation']=remediation(finding.get('action'));return finding
 def build(self):
  devices=self._devices();network=dict(self.links.snapshot);video=self._video();bundle=diagnostic_bundle(self.version,devices=devices,network=network,video=video,protocols={'active':self.telemetry.name,'available':self.telemetry.available,'error':self.telemetry.error,'telemetry':dict(self.telemetry.telemetry)},updater={'state':self.updater.updateState,'status':self.updater.updateStatus,'availableVersion':self.updater.availableVersion,'progress':self.updater.progress},events=self.events.snapshot());bundle['networkHealth']=self._network_health(network,video,devices);return bundle
 @Property('QVariantMap',notify=changed)
 def snapshot(self):return self.build()
 @Slot(result=str)
 def export(self):
  path=self.data_dir/'diagnostics'/'diagnostic-bundle.json';export_bundle(path,self.build());self.events.record('diagnostics','info','diagnostic bundle exported',detail={'path':str(path)});self.changed.emit();return str(path)
