import socket,time
from datetime import datetime,timezone
from PySide6.QtCore import QObject,Property,Signal,Slot

class VideoRuntime(QObject):
 changed=Signal();notice=Signal(str)
 def __init__(self,devices):
  super().__init__();self.devices=devices;self._state='stopped';self._error='';self._stream_id='';self._url='';self._host='';self._port=0;self._attempts=0;self._last_event='';self._stream={};self._profile={};self._device={};self._check_ms=None
 @Property(str,notify=changed)
 def state(self):return self._state
 @Property(str,notify=changed)
 def error(self):return self._error
 @Property(str,notify=changed)
 def streamId(self):return self._stream_id
 @Property(str,notify=changed)
 def url(self):return self._url
 @Property(bool,notify=changed)
 def running(self):return self._state in ('ready','playing')
 @Property(int,notify=changed)
 def attempts(self):return self._attempts
 @Property(str,notify=changed)
 def lastEvent(self):return self._last_event
 @Property('QVariantMap',notify=changed)
 def diagnostics(self):
  p=self._profile if self._stream_id else {};s=self._stream if self._stream_id else {}
  return {'state':self._state,'error':self._error or None,'streamId':self._stream_id or None,'streamName':s.get('name'),'kind':s.get('kind'),'protocol':s.get('protocol'),'host':self._host or None,'port':self._port or None,'path':s.get('path'),'codec':p.get('codec'),'width':p.get('width'),'height':p.get('height'),'fps':p.get('fps'),'latencyMode':p.get('latency_mode'),'endpointCheckMs':self._check_ms,'attempts':self._attempts,'lastEvent':self._last_event or None}
 def _set(self,state,error=''):self._state=state;self._error=error;self._last_event=datetime.now(timezone.utc).isoformat();self.changed.emit()
 def _clear_selection(self):self._stream_id='';self._url='';self._host='';self._port=0;self._attempts=0;self._stream={};self._profile={};self._device={};self._check_ms=None
 def _canonical_stream(self,stream):
  value=dict(stream);path=str(value.get('path','')).strip();value['path']=path if not path or path.startswith('/') else '/'+path;return value
 def _current_source(self,stream_id):
  stream=next((s for s in self.devices.activeStreams if s.get('id')==stream_id and s.get('enabled')),None)
  if not stream:return None,None,None
  device=next((d for d in self.devices.items if d.get('id')==stream.get('device_id')),None)
  if not device:return stream,None,None
  profile=next((p for p in self.devices.videoProfiles if p.get('id')==stream.get('video_profile_id')),None) if stream.get('video_profile_id') else {}
  return stream,device,profile
 def _source_unchanged(self):
  if not self._stream_id:return False
  stream,device,profile=self._current_source(self._stream_id)
  return stream is not None and device is not None and profile is not None and self._canonical_stream(stream)==self._stream and dict(device)==self._device and dict(profile)==self._profile
 def invalidateIfSourceChanged(self):
  if self._stream_id and not self._source_unchanged():
   self._clear_selection();self._set('error','Підготовлений відеопотік змінено, вимкнено, видалено або він більше не належить активному пристрою');return True
  return False
 def _check_endpoint(self):
  start=time.monotonic()
  try:
   with socket.create_connection((self._host,self._port),timeout=1.5):pass
  except OSError as exc:self._check_ms=round((time.monotonic()-start)*1000);self._set('error',f'RTSP {self._host}:{self._port} недоступний: {exc}');return False
  self._check_ms=round((time.monotonic()-start)*1000);return True
 @Slot(str,result=bool)
 def prepare(self,stream_id):
  stream,device,profile=self._current_source(stream_id)
  if not stream:self._clear_selection();self._set('error','Відеопотік не знайдено, вимкнений або не належить активному пристрою');return False
  if not device:self._clear_selection();self._set('error','Камеру для відеопотоку не знайдено');return False
  if profile is None:self._clear_selection();self._set('error','Video profile для потоку більше не існує');return False
  if str(stream.get('protocol','')).lower()!='rtsp':self._clear_selection();self._set('error','Поточний runtime підтримує лише RTSP');return False
  try:port=int(stream.get('port'))
  except (TypeError,ValueError):port=0
  host=str(device.get('host','')).strip();canonical=self._canonical_stream(stream);path=canonical.get('path','')
  if not host or port<1 or port>65535 or not path:self._clear_selection();self._set('error','RTSP endpoint metadata incomplete or invalid');return False
  self._stream=canonical;self._device=dict(device);self._profile=dict(profile);self._host=host;self._port=port;self._stream_id=stream_id;self._url=f'rtsp://{self._host}:{self._port}{path}';self._attempts=1;self._set('checking')
  if not self._check_endpoint():return False
  self._set('ready');return True
 @Slot(result=bool)
 def reconnect(self):
  if not self._url or not self._host or not self._port:self._set('error','Немає підготовленого RTSP-потоку для перепідключення');return False
  if not self._source_unchanged():self._clear_selection();self._set('error','Підготовлений RTSP-потік або його metadata змінилися; потрібна нова підготовка');return False
  self._attempts+=1;self._set('reconnecting')
  if not self._check_endpoint():return False
  self._set('ready');return True
 @Slot()
 def markPlaying(self):
  if self._url and self._source_unchanged() and self._state in ('ready','reconnecting'):self._set('playing')
  elif self._stream_id and not self._source_unchanged():self.invalidateIfSourceChanged()
 @Slot(str)
 def playbackError(self,message):
  if self._stream_id and self._source_unchanged():self._set('error',message or 'Помилка відтворення RTSP')
  elif self._stream_id:self.invalidateIfSourceChanged()
 @Slot(str)
 def markStalled(self,message=''):
  if self._stream_id and self._source_unchanged():self._set('stalled',message or 'RTSP-потік зупинився або перестав віддавати кадри')
  elif self._stream_id:self.invalidateIfSourceChanged()
 @Slot()
 def stop(self):self._clear_selection();self._set('stopped')

class VideoWorkspaceRuntime(QObject):
 changed=Signal()
 def __init__(self,devices):
  super().__init__();self.devices=devices;self.primary=VideoRuntime(devices);self.secondary=VideoRuntime(devices);self._pip=False
  for name in ('streamsChanged','changed','profilesChanged'):
   signal=getattr(devices,name,None)
   if signal is not None:signal.connect(self.reconcile)
 @Property(bool,notify=changed)
 def pipEnabled(self):return self._pip
 @Slot()
 def reconcile(self):
  self.primary.invalidateIfSourceChanged();secondary_invalid=self.secondary.invalidateIfSourceChanged()
  if secondary_invalid and self._pip:self._pip=False;self.changed.emit()
 @Slot(str,result=bool)
 def preparePrimary(self,stream_id):
  self.reconcile()
  if stream_id and stream_id==self.secondary.streamId:self.secondary.stop()
  return self.primary.prepare(stream_id)
 @Slot(str,result=bool)
 def prepareSecondary(self,stream_id):
  self.reconcile()
  if not self._pip or not stream_id or stream_id==self.primary.streamId:return False
  return self.secondary.prepare(stream_id)
 @Slot(bool)
 def setPipEnabled(self,enabled):
  enabled=bool(enabled)
  if self._pip==enabled:return
  self._pip=enabled
  if not enabled:self.secondary.stop()
  self.changed.emit()
 @Slot()
 def stopAll(self):self._pip=False;self.primary.stop();self.secondary.stop();self.changed.emit()
