"""Read-only MSP v1/v2 parsing and telemetry runtime."""
from __future__ import annotations
import struct,time
from dataclasses import dataclass
from PySide6.QtCore import QCoreApplication,QObject,Property,QTimer,Signal,Slot
MSP_API_VERSION=1;MSP_FC_VARIANT=2;MSP_FC_VERSION=3;MSP_STATUS=101;MSP_RAW_GPS=106;MSP_ATTITUDE=108;MSP_ALTITUDE=109;MSP_ANALOG=110
READ_ONLY_COMMANDS=(MSP_API_VERSION,MSP_FC_VARIANT,MSP_FC_VERSION,MSP_STATUS,MSP_RAW_GPS,MSP_ATTITUDE,MSP_ALTITUDE,MSP_ANALOG)
def crc8_dvb_s2(data):
 crc=0
 for value in data:
  crc^=value
  for _ in range(8):crc=((crc<<1)^0xD5)&255 if crc&0x80 else (crc<<1)&255
 return crc
def build_request(command,version=1):
 if command not in READ_ONLY_COMMANDS:raise ValueError(f'MSP command {command} is not allowed by the read-only runtime')
 if version==1:
  if command>255:raise ValueError('MSP v1 command must fit in one byte')
  return b'$M<'+bytes((0,command,command))
 if version==2:
  body=struct.pack('<BHH',0,command,0);return b'$X<'+body+bytes((crc8_dvb_s2(body),))
 raise ValueError('MSP version must be 1 or 2')
@dataclass(frozen=True)
class MspFrame:version:int;direction:str;command:int;payload:bytes
class MspParser:
 def __init__(self):self._buffer=bytearray();self.checksum_errors=0;self.frames=0
 def feed(self,data):
  self._buffer.extend(data);result=[]
  while True:
   start=self._buffer.find(b'$')
   if start<0:self._buffer.clear();break
   if start:del self._buffer[:start]
   if len(self._buffer)<3:break
   marker=bytes(self._buffer[:2]);parsed=self._parse_v1() if marker==b'$M' else self._parse_v2() if marker==b'$X' else False
   if parsed is None:break
   if parsed is False:
    if self._buffer:del self._buffer[0]
    continue
   result.append(parsed);self.frames+=1
  return result
 def _parse_v1(self):
  if len(self._buffer)<6:return None
  direction=chr(self._buffer[2])
  if direction not in '>!':return False
  size,command=self._buffer[3],self._buffer[4];total=6+size
  if len(self._buffer)<total:return None
  payload=bytes(self._buffer[5:5+size]);checksum=size^command
  for value in payload:checksum^=value
  received=self._buffer[5+size];del self._buffer[:total]
  if checksum!=received:self.checksum_errors+=1;return False
  return MspFrame(1,direction,command,payload)
 def _parse_v2(self):
  if len(self._buffer)<9:return None
  direction=chr(self._buffer[2])
  if direction not in '>!':return False
  command=int.from_bytes(self._buffer[4:6],'little');size=int.from_bytes(self._buffer[6:8],'little');total=9+size
  if len(self._buffer)<total:return None
  body=bytes(self._buffer[3:8+size]);payload=bytes(self._buffer[8:8+size]);received=self._buffer[8+size];del self._buffer[:total]
  if crc8_dvb_s2(body)!=received:self.checksum_errors+=1;return False
  return MspFrame(2,direction,command,payload)
class MspRuntime(QObject):
 changed=Signal();STALE_SECONDS=3.0
 def __init__(self,clock=time.monotonic):
  super().__init__();self._clock=clock;self._parser=MspParser();self._values={};self._updated={};self._last_frame=None;self._error='';self._fc_variant='';self._fc_version='';self._api_version='';self._expiry_timer=QTimer(self);self._expiry_timer.setInterval(250);self._expiry_timer.timeout.connect(self._refresh_freshness)
 @Property('QVariantMap',notify=changed)
 def telemetry(self):
  now=self._clock();observed=self._last_frame is not None;fresh=observed and now-self._last_frame<=self.STALE_SECONDS;data={k:v for k,v in self._values.items() if now-self._updated.get(k,0)<=self.STALE_SECONDS}
  data.update({'connected':True if fresh else (False if observed else None),'armed':None,'flightMode':None,'health':'ok' if fresh else ('stale' if observed else None),'ages':{k:round(now-v,3) for k,v in self._updated.items()},'freshness':{k:now-stamp<=self.STALE_SECONDS for k,stamp in self._updated.items()},'link':{'protocol':'MSP','fcVariant':self._fc_variant or None,'fcVersion':self._fc_version or None,'apiVersion':self._api_version or None,'frames':self._parser.frames,'checksumErrors':self._parser.checksum_errors}});return data
 @Property(str,notify=changed)
 def error(self):return self._error
 @Slot(bytes)
 def feed(self,data):
  changed=False
  for frame in self._parser.feed(data):
   self._last_frame=self._clock();changed=True
   if frame.direction=='!':self._error=f'MSP: відповідь із помилкою для команди {frame.command}'
   else:self._decode(frame.command,frame.payload);self._error=''
  if changed:
   if QCoreApplication.instance() is not None and not self._expiry_timer.isActive():self._expiry_timer.start()
   self.changed.emit()
 def _refresh_freshness(self):
  if self._last_frame is None or self._clock()-self._last_frame>self.STALE_SECONDS:self._expiry_timer.stop()
  self.changed.emit()
 def _set(self,values):stamp=self._clock();self._values.update(values);self._updated.update({k:stamp for k in values})
 def _decode(self,command,payload):
  if command==MSP_API_VERSION and len(payload)>=3:self._api_version=f'{payload[1]}.{payload[2]}'
  elif command==MSP_FC_VARIANT and len(payload)>=4:self._fc_variant=payload[:4].decode('ascii','replace')
  elif command==MSP_FC_VERSION and len(payload)>=3:self._fc_version='.'.join(str(v) for v in payload[:3])
  elif command==MSP_ATTITUDE and len(payload)>=6:roll,pitch,yaw=struct.unpack_from('<hhh',payload);self._set({'roll':roll/10,'pitch':pitch/10,'yaw':float(yaw)})
  elif command==MSP_ALTITUDE and len(payload)>=4:self._set({'altitude':struct.unpack_from('<i',payload)[0]/100})
  elif command==MSP_ANALOG and len(payload)>=7:voltage,_mah,rssi,current=struct.unpack_from('<BHHH',payload);self._set({'batteryVoltage':voltage/10,'current':current/100,'rssi':rssi})
  elif command==MSP_RAW_GPS and len(payload)>=16:fix,sats,_lat,_lon,alt,speed,course=struct.unpack_from('<BBiihHH',payload);self._set({'gpsFix':fix,'satellites':sats,'altitude':float(alt),'groundSpeed':speed/100,'heading':course/10})
