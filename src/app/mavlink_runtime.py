import math
import threading
import time
from PySide6.QtCore import QObject, Property, QSettings, QThread, Signal, Slot
from pymavlink import mavutil

DEFAULT_ENDPOINT = "udpin:0.0.0.0:14550"
HEARTBEAT_TIMEOUT = 3.0
STALE_AFTER = {"heartbeat":3.0,"battery":5.0,"gps":5.0,"position":3.0,"attitude":2.0,"radio":5.0,"home":30.0}
GROUP_FIELDS = {
 "heartbeat":("armed","flightMode"),
 "battery":("batteryVoltage","current","batteryRemaining"),
 "gps":("gpsFix","satellites","hdop"),
 "position":("altitude","groundSpeed","heading","homeDistance"),
 "attitude":("roll","pitch","yaw"),
 "radio":("rssi","rssiSource"),
 "home":(),
}

def _num(value, scale=1.0, invalid=None):
 if value is None or value == invalid:return None
 try:return float(value)/scale
 except (TypeError,ValueError):return None

def _distance_m(a,b):
 if not a or not b:return None
 lat1,lon1=map(math.radians,a);lat2,lon2=map(math.radians,b);dlat,dlon=lat2-lat1,lon2-lon1
 h=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
 return 6371000.0*2*math.atan2(math.sqrt(h),math.sqrt(max(0.0,1.0-h)))

class MavlinkWorker(QThread):
 telemetry=Signal(object);failed=Signal(str)
 def __init__(self,endpoint,baud):
  super().__init__();self.endpoint=endpoint;self.baud=baud;self._stop=threading.Event();self._master=None;self._data={};self._seen={};self._home=None;self._position=None;self._last_heartbeat=0.0
 def stop(self):
  self._stop.set()
  if self._master is not None:
   try:self._master.close()
   except Exception:pass
 def _touch(self,group):self._seen[group]=time.monotonic()
 def _snapshot(self):
  now=time.monotonic();out=dict(self._data);ages={}
  for group,limit in STALE_AFTER.items():
   seen=self._seen.get(group);age=None if seen is None else max(0.0,now-seen);ages[group]=age
   fresh=age is not None and age<limit;out[group+"Fresh"]=fresh
   if not fresh:
    for field in GROUP_FIELDS[group]:out[field]=None
  connected=self._last_heartbeat>0 and now-self._last_heartbeat<HEARTBEAT_TIMEOUT
  out["connected"]=connected;out["heartbeat"]=connected;out["ages"]=ages
  return out
 def _emit(self,group=None,**values):
  if group:self._touch(group)
  self._data.update(values);self.telemetry.emit(self._snapshot())
 def _handle(self,msg):
  kind=msg.get_type()
  if kind=="BAD_DATA":return
  if kind=="HEARTBEAT":
   self._last_heartbeat=time.monotonic();armed=bool(msg.base_mode&mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
   try:mode=mavutil.mode_string_v10(msg)
   except Exception:mode="UNKNOWN"
   self._emit("heartbeat",armed=armed,flightMode=mode);return
  if kind=="SYS_STATUS":self._emit("battery",batteryVoltage=_num(msg.voltage_battery,1000.0,65535),current=_num(msg.current_battery,100.0,-1),batteryRemaining=_num(msg.battery_remaining,1.0,-1))
  elif kind=="BATTERY_STATUS":
   cells=getattr(msg,"voltages",None) or [];valid=[v for v in cells if 0<v<65535];voltage=sum(valid)/1000.0 if valid else self._data.get("batteryVoltage")
   self._emit("battery",batteryVoltage=voltage,current=_num(getattr(msg,"current_battery",None),100.0,-1),batteryRemaining=_num(getattr(msg,"battery_remaining",None),1.0,-1))
  elif kind=="GPS_RAW_INT":
   sats=int(getattr(msg,"satellites_visible",0));eph=getattr(msg,"eph",65535)
   self._emit("gps",gpsFix=int(getattr(msg,"fix_type",0)),satellites=None if sats==255 else sats,hdop=None if eph==65535 else eph/100.0)
  elif kind=="GLOBAL_POSITION_INT":
   self._position=(msg.lat/1e7,msg.lon/1e7);hdg=getattr(msg,"hdg",65535)
   self._emit("position",altitude=msg.relative_alt/1000.0,heading=None if hdg==65535 else hdg/100.0,homeDistance=_distance_m(self._home,self._position))
  elif kind=="VFR_HUD":self._emit("position",groundSpeed=float(msg.groundspeed),heading=float(msg.heading),altitude=float(msg.alt),homeDistance=_distance_m(self._home,self._position))
  elif kind=="ATTITUDE":self._emit("attitude",roll=math.degrees(msg.roll),pitch=math.degrees(msg.pitch),yaw=math.degrees(msg.yaw))
  elif kind=="RADIO_STATUS":self._emit("radio",rssi=int(msg.rssi) if getattr(msg,"rssi",255)!=255 else None,rssiSource="RADIO_STATUS")
  elif kind=="RC_CHANNELS":self._emit("radio",rssi=int(msg.rssi) if getattr(msg,"rssi",255)!=255 else None,rssiSource="RC_CHANNELS")
  elif kind=="HOME_POSITION":
   lat,lon=msg.latitude/1e7,msg.longitude/1e7
   if lat or lon:self._home=(lat,lon);self._touch("home")
   self._emit("position",homeDistance=_distance_m(self._home,self._position))
 def run(self):
  try:
   kwargs={"autoreconnect":True,"robust_parsing":True}
   if not self.endpoint.startswith(("udp","tcp")):kwargs["baud"]=self.baud
   self._master=mavutil.mavlink_connection(self.endpoint,**kwargs);self._emit()
   while not self._stop.is_set():
    msg=self._master.recv_match(blocking=True,timeout=.25)
    if msg is not None:self._handle(msg)
    else:self.telemetry.emit(self._snapshot())
  except Exception as exc:
   if not self._stop.is_set():self.failed.emit(str(exc))
  finally:
   if self._master is not None:
    try:self._master.close()
    except Exception:pass
   self._master=None

class MavlinkRuntime(QObject):
 changed=Signal()
 def __init__(self):
  super().__init__();settings=QSettings("FPV-Uhyliant","FPV-Uhyliant");self._endpoint=str(settings.value("mavlink/endpoint",DEFAULT_ENDPOINT));self._baud=int(settings.value("mavlink/baud",115200));self._enabled=str(settings.value("mavlink/enabled","true")).lower() not in ("0","false");self._worker=None;self._error="";self._telemetry={"connected":False,"heartbeat":False};self._generation=0
  if self._enabled:self.start()
 @Property(str,notify=changed)
 def endpoint(self):return self._endpoint
 @Property(int,notify=changed)
 def baud(self):return self._baud
 @Property(bool,notify=changed)
 def enabled(self):return self._enabled
 @Property(bool,notify=changed)
 def running(self):return self._worker is not None and self._worker.isRunning()
 @Property(str,notify=changed)
 def error(self):return self._error
 @Property("QVariantMap",notify=changed)
 def telemetry(self):return self._telemetry
 @Slot(str,int,bool)
 def configure(self,endpoint,baud,enabled):
  endpoint=endpoint.strip()
  if not endpoint:self._error="MAVLink endpoint не може бути порожнім";self.changed.emit();return
  self.stop();self._endpoint=endpoint;self._baud=max(1200,min(int(baud),4000000));self._enabled=bool(enabled);settings=QSettings("FPV-Uhyliant","FPV-Uhyliant");settings.setValue("mavlink/endpoint",self._endpoint);settings.setValue("mavlink/baud",self._baud);settings.setValue("mavlink/enabled",self._enabled);self._error="";self.changed.emit()
  if self._enabled:self.start()
 @Slot()
 def start(self):
  if self._worker is not None:return
  self._generation+=1;generation=self._generation;self._error="";worker=MavlinkWorker(self._endpoint,self._baud);self._worker=worker
  worker.telemetry.connect(lambda values,g=generation:self._on_telemetry(g,values));worker.failed.connect(lambda error,g=generation:self._on_error(g,error));worker.finished.connect(lambda g=generation,w=worker:self._on_finished(g,w));worker.start();self.changed.emit()
 @Slot()
 def stop(self):
  self._generation+=1;worker=self._worker;self._worker=None
  if worker is not None:
   worker.stop();worker.wait(1500)
  self._telemetry={"connected":False,"heartbeat":False};self.changed.emit()
 def _on_telemetry(self,generation,values):
  if generation!=self._generation:return
  self._telemetry=dict(values);self.changed.emit()
 def _on_error(self,generation,error):
  if generation!=self._generation:return
  self._error=error;self.changed.emit()
 def _on_finished(self,generation,worker):
  if generation==self._generation and worker is self._worker:self._worker=None
  worker.deleteLater();self.changed.emit()
 def shutdown(self):self.stop()
