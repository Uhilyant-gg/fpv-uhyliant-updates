import socket
from PySide6.QtCore import QObject, Property, Signal, Slot

class VideoRuntime(QObject):
    changed=Signal(); notice=Signal(str)
    def __init__(self,devices):
        super().__init__();self.devices=devices;self._state='stopped';self._error='';self._stream_id='';self._url=''
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
    def _set(self,state,error=''):self._state=state;self._error=error;self.changed.emit()
    @Slot(str,result=bool)
    def prepare(self,stream_id):
        stream=next((s for s in self.devices.streams if s['id']==stream_id and s.get('enabled')),None)
        if not stream:self._set('error','Відеопотік не знайдено або вимкнений');return False
        device=next((d for d in self.devices.items if d['id']==stream['device_id']),None)
        if not device:self._set('error','Камеру для відеопотоку не знайдено');return False
        if stream['protocol'].lower()!='rtsp':self._set('error','Поточний runtime підтримує лише RTSP');return False
        host=device['host'];port=int(stream['port']);path=stream['path'] if stream['path'].startswith('/') else '/'+stream['path']
        self._stream_id=stream_id;self._url=f'rtsp://{host}:{port}{path}';self._set('checking')
        try:
            with socket.create_connection((host,port),timeout=1.5):pass
        except OSError as e:self._set('error',f'RTSP {host}:{port} недоступний: {e}');return False
        self._set('ready');return True
    @Slot()
    def markPlaying(self):
        if self._url:self._set('playing')
    @Slot(str)
    def playbackError(self,message):self._set('error',message or 'Помилка відтворення RTSP')
    @Slot()
    def stop(self):self._stream_id='';self._url='';self._set('stopped')
