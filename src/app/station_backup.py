"""Versioned station backup export/import planning. Import never mutates live state directly."""
import hashlib,json
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot
SCHEMA='fpv-uhyliant-station-backup';VERSION=1
class StationBackup(QObject):
 changed=Signal()
 def __init__(self,devices):super().__init__();self.devices=devices;self._result={'ready':False,'reason':'Backup operation not started','manifest':{}}
 @Property('QVariantMap',notify=changed)
 def result(self):return dict(self._result)
 def _payload(self):return {'schema':SCHEMA,'version':VERSION,'devices':self.devices.exportSnapshot()}
 def _digest(self,payload):return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
 @Slot(str,result=bool)
 def exportTo(self,path):
  try:
   payload=self._payload();wrapper={'payload':payload,'sha256':self._digest(payload)};target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(wrapper,ensure_ascii=False,indent=2),encoding='utf-8');self._result={'ready':True,'reason':'Backup exported','manifest':{'schema':SCHEMA,'version':VERSION,'sha256':wrapper['sha256']}};self.changed.emit();return True
  except (OSError,TypeError,ValueError) as exc:self._result={'ready':False,'reason':'Backup export failed: '+str(exc),'manifest':{}};self.changed.emit();return False
 @Slot(str,result='QVariantMap')
 def inspectImport(self,path):
  try:
   wrapper=json.loads(Path(path).read_text(encoding='utf-8'));payload=wrapper.get('payload') if isinstance(wrapper,dict) else None;digest=wrapper.get('sha256') if isinstance(wrapper,dict) else None
   valid=bool(isinstance(payload,dict) and payload.get('schema')==SCHEMA and payload.get('version')==VERSION and isinstance(digest,str) and digest==self._digest(payload) and self.devices.validateSnapshot(payload.get('devices')))
   plan={'schema':SCHEMA,'version':VERSION,'sha256':digest,'deviceCount':len((payload or {}).get('devices',{}).get('devices',[])),'execution':'explicit-user-decision-required'} if valid else {}
   self._result={'ready':valid,'reason':'Restore plan verified; no live data changed' if valid else 'Backup is invalid, incompatible, or failed verification','manifest':plan};self.changed.emit();return dict(plan)
  except (OSError,TypeError,ValueError,json.JSONDecodeError):self._result={'ready':False,'reason':'Backup is invalid, incompatible, or unreadable','manifest':{}};self.changed.emit();return {}
