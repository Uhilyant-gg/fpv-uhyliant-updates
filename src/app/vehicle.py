import json
import os
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot

DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant'

class VehicleRuntime(QObject):
 changed=Signal()
 def __init__(self,mavlink,video):
  super().__init__();self.mavlink=mavlink;self.video=video;self._snapshot={};self._diagnostics={};mavlink.changed.connect(self.refresh);video.changed.connect(self.refresh);self.refresh()
 @Property('QVariantMap',notify=changed)
 def snapshot(self):return self._snapshot
 @Property('QVariantMap',notify=changed)
 def diagnostics(self):return self._diagnostics
 @Property(str,notify=changed)
 def health(self):return self._diagnostics.get('health','unknown')
 @Slot()
 def refresh(self):
  telemetry=dict(self.mavlink.telemetry or {});video_state=self.video.state
  self._snapshot={'protocol':'MAVLink','telemetry':telemetry,'video':{'state':video_state,'url':self.video.url,'attempts':self.video.attempts,'lastEvent':self.video.lastEvent}}
  issues=[]
  if self.mavlink.error:issues.append({'severity':'error','source':'MAVLink','message':self.mavlink.error})
  elif not telemetry.get('connected'):issues.append({'severity':'warning','source':'MAVLink','message':'Немає актуального HEARTBEAT'})
  if self.video.error:issues.append({'severity':'error' if video_state=='error' else 'warning','source':'RTSP','message':self.video.error})
  elif video_state=='stalled':issues.append({'severity':'warning','source':'RTSP','message':'Відеопотік зупинено'})
  health='error' if any(x['severity']=='error' for x in issues) else ('warning' if issues else 'ok')
  self._diagnostics={'health':health,'issues':issues,'generatedUtc':datetime.now(timezone.utc).isoformat(),'mavlinkHealth':telemetry.get('health','disconnected'),'videoState':video_state}
  self.changed.emit()
 @Slot(result=str)
 def exportReport(self):
  DATA.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%SZ');path=DATA/f'vehicle-diagnostics-{stamp}.json';path.write_text(json.dumps({'vehicle':self._snapshot,'diagnostics':self._diagnostics},ensure_ascii=False,indent=2),encoding='utf-8');return str(path)
