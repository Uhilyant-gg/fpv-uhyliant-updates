import socket
from datetime import datetime, timezone
from PySide6.QtCore import QObject, Property, Signal, Slot

class VideoRuntime(QObject):
    changed=Signal();notice=Signal(str)
    def __init__(self,devices):
        super().__init__();self.devices=devices;self._state='stopped';self._error='';self._stream_id='';self._url='';self._host='';self._port=0;self._attempts=0;self._last_event='';self._stream={}
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
        return {'state':self._state,'error':self._error or None,'streamId':self._stream_id or None,'streamName':self._stream.get('name'),'kind':self._stream.get('kind'),'protocol':self._stream.get('protocol'),'host':self._host or None,'port':self._port or None,'path':self._stream.get('path'),'attempts':self._attempts,'lastEvent':self._last_event or None}
    def _set(self,state,error=''):
        self._state=state;self._error=error;self._last_event=datetime.now(timezone.utc).isoformat();self.changed.emit()
    def _check_endpoint(self):
        try:
            with socket.create_connection((self._host,self._port),timeout=1.5):pass
        except OSError as exc:self._set('error',f'RTSP {self._host}:{self._port} недоступний: {exc}');return False
        return True
    @Slot(str,result=bool)
    def prepare(self,stream_id):
        stream=next((s for s in self.devices.streams if s['id']==stream_id and s.get('enabled')),None)
        if not stream:self._stream={};self._set('error','Відеопотік не знайдено або вимкнений');return False
        device=next((d for d in self.devices.items if d['id']==stream['device_id']),None)
        if not device:self._stream={};self._set('error','Камеру для відеопотоку не знайдено');return False
        if stream['protocol'].lower()!='rtsp':self._stream=dict(stream);self._set('error','Поточний runtime підтримує лише RTSP');return False
        self._stream=dict(stream);self._host=device['host'];self._port=int(stream['port']);path=stream['path'] if stream['path'].startswith('/') else '/'+stream['path'];self._stream['path']=path;self._stream_id=stream_id;self._url=f'rtsp://{self._host}:{self._port}{path}';self._attempts=1;self._set('checking')
        if not self._check_endpoint():return False
        self._set('ready');return True
    @Slot(result=bool)
    def reconnect(self):
        if not self._url or not self._host or not self._port:self._set('error','Немає підготовленого RTSP-потоку для перепідключення');return False
        self._attempts+=1;self._set('reconnecting')
        if not self._check_endpoint():return False
        self._set('ready');return True
    @Slot()
    def markPlaying(self):
        if self._url:self._set('playing')
    @Slot(str)
    def playbackError(self,message):self._set('error',message or 'Помилка відтворення RTSP')
    @Slot(str)
    def markStalled(self,message=''):self._set('stalled',message or 'RTSP-потік зупинився або перестав віддавати кадри')
    @Slot()
    def stop(self):
        self._stream_id='';self._url='';self._host='';self._port=0;self._attempts=0;self._stream={};self._set('stopped')
