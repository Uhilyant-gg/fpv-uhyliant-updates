"""Read-only CRSF parser/runtime; absent observations remain unavailable."""
from __future__ import annotations
import time
from dataclasses import dataclass
from PySide6.QtCore import QObject,Property,Signal,Slot
CRSF_FRAMETYPE_GPS=0x02;CRSF_FRAMETYPE_BATTERY_SENSOR=0x08;CRSF_FRAMETYPE_LINK_STATISTICS=0x14
def crc8_dvb_s2(data):
 crc=0
 for value in data:
  crc^=value
  for _ in range(8):crc=((crc<<1)^0xD5)&0xFF if crc&0x80 else (crc<<1)&0xFF
 return crc
@dataclass(frozen=True)
class CrsfFrame:address:int;frame_type:int;payload:bytes
class CrsfParser:
 def __init__(self):self._buffer=bytearray();self.frames=0;self.crc_errors=0
 def feed(self,data):
  self._buffer.extend(data);result=[]
  while len(self._buffer)>=2:
   length=self._buffer[1]
   if length<2 or length>64:del self._buffer[0];continue
   total=length+2
   if len(self._buffer)<total:break
   raw=bytes(self._buffer[:total]);del self._buffer[:total];frame_type=raw[2];payload=raw[3:-1]
   if crc8_dvb_s2(raw[2:-1])!=raw[-1]:self.crc_errors+=1;continue
   result.append(CrsfFrame(raw[0],frame_type,payload));self.frames+=1
  return result
class CrsfRuntime(QObject):
 changed=Signal();STALE_SECONDS=3.0
 def __init__(self,clock=time.monotonic):super().__init__();self._clock=clock;self._parser=CrsfParser();self._values={};self._updated={};self._last_frame=0.0;self._error=''
 @Property('QVariantMap',notify=changed)
 def telemetry(self):
  now=self._clock();observed=self._last_frame>0;fresh=observed and now-self._last_frame<=self.STALE_SECONDS;values={k:v for k,v in self._values.items() if now-self._updated.get(k,0)<=self.STALE_SECONDS}
  values.update({'connected':True if fresh else (False if observed else None),'armed':None,'flightMode':None,'health':'ok' if fresh else ('stale' if observed else None),'ages':{k:round(now-stamp,3) for k,stamp in self._updated.items()},'freshness':{k:now-stamp<=self.STALE_SECONDS for k,stamp in self._updated.items()},'link':{'protocol':'CRSF','frames':self._parser.frames,'crcErrors':self._parser.crc_errors}});return values
 @Property(str,notify=changed)
 def error(self):return self._error
 @Slot(bytes)
 def feed(self,data):
  frames=self._parser.feed(data)
  if not frames:return
  for frame in frames:self._last_frame=self._clock();self._decode(frame.frame_type,frame.payload)
  self.changed.emit()
 def _set(self,values):stamp=self._clock();self._values.update(values);self._updated.update({key:stamp for key in values})
 def _decode(self,frame_type,payload):
  if frame_type==CRSF_FRAMETYPE_BATTERY_SENSOR and len(payload)>=8:self._set({'batteryVoltage':int.from_bytes(payload[0:2],'big')/10.0,'current':int.from_bytes(payload[2:4],'big')/10.0,'batteryRemaining':payload[7]})
  elif frame_type==CRSF_FRAMETYPE_GPS and len(payload)>=15:self._set({'groundSpeed':int.from_bytes(payload[8:10],'big')/10.0,'heading':int.from_bytes(payload[10:12],'big')/100.0,'altitude':float(int.from_bytes(payload[12:14],'big')-1000),'satellites':payload[14]})
  elif frame_type==CRSF_FRAMETYPE_LINK_STATISTICS and len(payload)>=3:self._set({'rssi':payload[2]})
