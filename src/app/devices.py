import concurrent.futures, ipaddress, json, os, re, socket, sqlite3, threading, time, urllib.error, urllib.request, uuid
from pathlib import Path
import psutil
from PySide6.QtCore import QObject, Property, QThread, Signal, Slot
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

DATA=Path(os.environ.get("LOCALAPPDATA",Path.home()))/"FPV-Uhyliant"; LEGACY_DB=DATA/"devices.json"; DB=DATA/"devices.sqlite3"
SERVICES=("_http._tcp.local.","_rtsp._tcp.local.","_ssh._tcp.local."); WS_DISCOVERY=("239.255.255.250",3702); MAX_WORKERS=32; SCHEMA_VERSION=3
HOST_RE=re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*\.?$")
def valid_host(host):
 host=host.strip()
 if not host or "://" in host or "/" in host or "\\" in host or any(c.isspace() for c in host):return False
 try:ip=ipaddress.ip_address(host);return ip.version==4 and not(ip.is_unspecified or ip.is_multicast)
 except ValueError:return bool(HOST_RE.fullmatch(host))
def merge(found,host,name="",service="",verified=False,evidence=""):
 if not host:return
 i=found.setdefault(host,{"name":name or host,"host":host,"hostname":name or host,"services":[],"openipc":False,"evidence":[]})
 if name and i["name"]==host:i["name"]=name;i["hostname"]=name
 if service and service not in i["services"]:i["services"].append(service)
 if verified:i["openipc"]=True
 if evidence and evidence not in i["evidence"]:i["evidence"].append(evidence)
def interfaces():
 out=[];stats=psutil.net_if_stats()
 for name,addrs in psutil.net_if_addrs().items():
  if name in stats and not stats[name].isup:continue
  for a in addrs:
   if a.family!=socket.AF_INET or not a.address or a.address.startswith("127."):continue
   mask=a.netmask or "255.255.255.0"
   try:net=str(ipaddress.ip_network(f"{a.address}/{mask}",strict=False))
   except ValueError:net=str(ipaddress.ip_network(f"{a.address}/24",strict=False))
   out.append({"id":f"{name}|{a.address}","name":name,"address":a.address,"netmask":mask,"network":net,"label":f"{name} — {a.address} — {net}"})
 return out
def probe(host,cancel):
 if cancel.is_set():return host,False,[]
 try:ipaddress.ip_address(host)
 except ValueError:return host,False,[]
 evidence=[];verified=False
 for url,label,jmode in ((f"<scrubbed-url-domain>","Majestic /api/v1/config.json",True),(f"<scrubbed-url-domain>","OpenIPC/Majestic WebUI :85",False)):
  if cancel.is_set():break
  try:
   req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"FPV-Uhyliant"})
   with urllib.request.urlopen(req,timeout=.45) as r:raw=r.read(524288 if jmode else 65536)
   if jmode:
    data=json.loads(raw.decode());matched=isinstance(data,dict) and data and any(k in data for k in ("video0","video1","system","fpv","isp","rtsp"))
   else:body=raw.decode("utf-8","ignore").lower();matched="openipc" in body or "majestic" in body
   if matched:verified=True;evidence.append(label)
  except (urllib.error.URLError,TimeoutError,socket.timeout,UnicodeError,json.JSONDecodeError,OSError):pass
 return host,verified,evidence
def onvif(found,cancel,bind_ip,network):
 for probe_type in ("dn:NetworkVideoTransmitter",""):
  if cancel.is_set():return
  mid=str(uuid.uuid4());types=f"<d:Types>{probe_type}</d:Types>" if probe_type else "";payload=('<?xml version="1.0"?><e:Envelope xmlns:e="http://<scrubbed-url-domain>/2003/05/soap-envelope" xmlns:w="http://<scrubbed-url-domain>/ws/2004/08/addressing" xmlns:d="http://<scrubbed-url-domain>/ws/2005/04/discovery" xmlns:dn="http://<scrubbed-url-domain>/ver10/network/wsdl"><e:Header><w:MessageID>uuid:'+mid+'</w:MessageID><w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To><w:Action>http://<scrubbed-url-domain>/ws/2005/04/discovery/Probe</w:Action></e:Header><e:Body><d:Probe>'+types+'</d:Probe></e:Body></e:Envelope>').encode()
  s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
  try:
   s.bind((bind_ip,0));s.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_IF,socket.inet_aton(bind_ip));s.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,2);s.settimeout(.2)
   for _ in range(2):s.sendto(payload,WS_DISCOVERY)
   deadline=time.monotonic()+2.5
   while time.monotonic()<deadline and not cancel.is_set():
    try:data,source=s.recvfrom(65535)
    except socket.timeout:continue
    host=source[0]
    try:
     if ipaddress.ip_address(host) not in network:continue
    except ValueError:continue
    hint="openipc" in data.decode("utf-8","ignore").lower();merge(found,host,"ONVIF "+host,"ONVIF",False,"ONVIF OpenIPC hint" if hint else "ONVIF WS-Discovery")
  finally:s.close()
def host_sort_key(i):
 try:h=(0,int(ipaddress.ip_address(i["host"])))
 except ValueError:h=(1,i["host"].lower())
 return not i["openipc"],h
class Worker(QThread):
 done=Signal(object,bool,str);progress=Signal(str,int,int,int);live=Signal(object)
 def __init__(self,iface):super().__init__();self.cancel=threading.Event();self.iface=iface
 def stop(self):self.cancel.set();self.requestInterruption()
 def emit_progress(self,s,d=0,t=0,f=0):self.progress.emit(s,d,t,f)
 def run(self):
  found={};worker=self;bind_ip=self.iface["address"];net=ipaddress.ip_network(self.iface["network"],strict=False)
  try:
   self.emit_progress("mDNS")
   class Listener(ServiceListener):
    def add_service(self,z,t,n):
     if worker.cancel.is_set():return
     try:
      info=z.get_service_info(t,n,timeout=800)
      if not info:return
      p={k.decode(errors="ignore").lower():v.decode(errors="ignore") for k,v in info.properties.items()};server=(info.server or "").rstrip(".");verified=p.get("vendor","").strip().lower()=="openipc";hint="openipc" in n.lower() or "openipc" in server.lower();ev="mDNS vendor=OpenIPC" if verified else ("mDNS OpenIPC name hint" if hint else "mDNS")
      for host in info.parsed_addresses():
       try:
        if ipaddress.ip_address(host) not in net:continue
       except ValueError:continue
       merge(found,host,server or n.split(".")[0],t,verified,ev)
      worker.live.emit(list(found.values()));worker.emit_progress("mDNS",f=len(found))
     except (OSError,UnicodeError,ValueError):pass
    def update_service(self,z,t,n):self.add_service(z,t,n)
    def remove_service(self,z,t,n):pass
   z=Zeroconf(interfaces=[bind_ip]);listener=Listener();browsers=[ServiceBrowser(z,s,listener) for s in SERVICES];deadline=time.monotonic()+3.5
   while time.monotonic()<deadline and not self.cancel.is_set():self.msleep(100)
   for b in browsers:b.cancel()
   z.close()
   if not self.cancel.is_set():self.emit_progress("ONVIF",f=len(found));onvif(found,self.cancel,bind_ip,net);self.live.emit(list(found.values()))
   if not self.cancel.is_set():
    targets=list(found);self.emit_progress("fingerprint",0,len(targets),len(found))
    for idx,host in enumerate(targets,1):
     if self.cancel.is_set():break
     _,verified,evidence=probe(host,self.cancel)
     if verified:
      merge(found,host,service="Majestic/OpenIPC fingerprint",verified=True)
      for reason in evidence:merge(found,host,evidence=reason)
     self.emit_progress("fingerprint",idx,len(targets),len(found));self.live.emit(list(found.values()))
   if not self.cancel.is_set():
    hosts=[str(h) for h in ipaddress.ip_network(bind_ip+"/24",strict=False).hosts() if str(h)!=bind_ip];total=len(hosts);completed=0;self.emit_progress("/24",0,total,len(found));ex=concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS);pending={ex.submit(probe,h,self.cancel) for h in hosts}
    try:
     while pending and not self.cancel.is_set():
      finished,pending=concurrent.futures.wait(pending,timeout=.1,return_when=concurrent.futures.FIRST_COMPLETED)
      for fut in finished:
       completed+=1
       try:host,verified,evidence=fut.result()
       except Exception:continue
       if verified:
        merge(found,host,"OpenIPC "+host,"/24 fingerprint",True)
        for reason in evidence:merge(found,host,evidence=reason)
       self.emit_progress("/24",completed,total,len(found))
      if finished:self.live.emit(list(found.values()))
    finally:
     if self.cancel.is_set():
      for fut in pending:fut.cancel()
     ex.shutdown(wait=not self.cancel.is_set(),cancel_futures=True)
   result=list(found.values())
   for i in result:i["confidence"]="OpenIPC підтверджено" if i["openipc"] else "Кандидат, не підтверджено"
   result.sort(key=host_sort_key);self.done.emit(result,self.cancel.is_set(),"")
  except Exception as e:self.done.emit(list(found.values()),self.cancel.is_set(),str(e))
class Devices(QObject):
 changed=Signal();notice=Signal(str);discoveryChanged=Signal();streamsChanged=Signal();profilesChanged=Signal()
 def __init__(self):
  super().__init__();DATA.mkdir(parents=True,exist_ok=True);self._items=[];self._active_id="";self._streams=[];self._profiles=[];self._discovered=[];self._scanning=False;self._worker=None;self._stage="Готово";self._pd=self._pt=self._found=0;self._status="Готово";self._interfaces=[];self._selected_interface="";self._init_db();self._load();self.refreshInterfaces()
 def _connect(self):db=sqlite3.connect(DB,timeout=5);db.execute("PRAGMA foreign_keys=ON");return db
 def _init_db(self):
  with self._connect() as db:
   db.execute("PRAGMA journal_mode=WAL");db.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)");ver=db.execute("PRAGMA user_version").fetchone()[0]
   db.execute("CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY,name TEXT NOT NULL,type TEXT NOT NULL,host TEXT NOT NULL,port INTEGER NOT NULL,connection TEXT NOT NULL,notes TEXT NOT NULL)");db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_host_port ON devices(host,port)")
   if ver<2:
    db.execute("CREATE TABLE IF NOT EXISTS streams(id TEXT PRIMARY KEY,device_id TEXT NOT NULL,name TEXT NOT NULL,kind TEXT NOT NULL DEFAULT 'main',protocol TEXT NOT NULL DEFAULT 'rtsp',port INTEGER NOT NULL DEFAULT 554,path TEXT NOT NULL DEFAULT '/',video_profile_id TEXT,enabled INTEGER NOT NULL DEFAULT 1,FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE)");db.execute("CREATE INDEX IF NOT EXISTS idx_streams_device ON streams(device_id)");db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_streams_device_kind ON streams(device_id,kind)")
   if ver<3:
    db.execute("CREATE TABLE IF NOT EXISTS video_profiles(id TEXT PRIMARY KEY,name TEXT NOT NULL UNIQUE,codec TEXT NOT NULL DEFAULT 'h264',width INTEGER,height INTEGER,fps INTEGER,bitrate_kbps INTEGER,latency_mode TEXT NOT NULL DEFAULT 'balanced',notes TEXT NOT NULL DEFAULT '')")
    defaults=(("low-latency","Мінімальна затримка","h264",None,None,60,None,"low_latency",""),("balanced","Збалансований","h264",None,None,30,None,"balanced",""),("low-bitrate","Низький бітрейт","h264",None,None,30,2000,"balanced",""),("max-quality","Максимальна якість","h265",None,None,30,None,"quality",""))
    db.executemany("INSERT OR IGNORE INTO video_profiles VALUES(?,?,?,?,?,?,?,?,?)",defaults);db.execute("PRAGMA user_version=3")
   if db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]==0 and LEGACY_DB.exists():
    try:
     raw=json.loads(LEGACY_DB.read_text(encoding="utf-8"));items=raw.get("devices",[]) if isinstance(raw,dict) else []
     for i in items:
      host=str(i.get("host","")).strip()
      if i.get("id") and i.get("name") and valid_host(host):db.execute("INSERT OR IGNORE INTO devices VALUES(?,?,?,?,?,?,?)",(i["id"],i["name"],i.get("type","Пристрій"),host,max(1,min(int(i.get("port",80)),65535)),i.get("connection","Мережа"),i.get("notes","")))
     db.execute("INSERT OR REPLACE INTO settings VALUES('activeDeviceId',?)",(raw.get("activeDeviceId",""),));LEGACY_DB.rename(LEGACY_DB.with_suffix(".json.migrated"))
    except (OSError,ValueError,TypeError,json.JSONDecodeError):pass
 def _load(self):
  try:
   with self._connect() as db:
    cols="id,name,type,host,port,connection,notes";self._items=[dict(zip(cols.split(','),r)) for r in db.execute("SELECT "+cols+" FROM devices ORDER BY name COLLATE NOCASE")]
    row=db.execute("SELECT value FROM settings WHERE key='activeDeviceId'").fetchone();saved=row[0] if row else ""
   self._active_id=saved if any(i["id"]==saved for i in self._items) else ""
   self._load_streams();self._load_profiles()
  except sqlite3.Error as e:self._items=[];self._streams=[];self._profiles=[];self._active_id="";self.notice.emit("Помилка бази пристроїв: "+str(e))
 def _load_streams(self):
  with self._connect() as db:cols="id,device_id,name,kind,protocol,port,path,video_profile_id,enabled";self._streams=[dict(zip(cols.split(','),r)) for r in db.execute("SELECT "+cols+" FROM streams ORDER BY device_id,kind,name")]
  for s in self._streams:s["enabled"]=bool(s["enabled"])
  self.streamsChanged.emit()
 def _load_profiles(self):
  with self._connect() as db:cols="id,name,codec,width,height,fps,bitrate_kbps,latency_mode,notes";self._profiles=[dict(zip(cols.split(','),r)) for r in db.execute("SELECT "+cols+" FROM video_profiles ORDER BY name COLLATE NOCASE")]
  self.profilesChanged.emit()
 def _save_active(self):
  with self._connect() as db:db.execute("INSERT OR REPLACE INTO settings VALUES('activeDeviceId',?)",(self._active_id,))
 def _public_item(self,i):return {**i,"active":i["id"]==self._active_id}
 @Property("QVariantList",notify=changed)
 def items(self):return [self._public_item(i) for i in self._items]
 @Property(int,notify=changed)
 def count(self):return len(self._items)
 @Property(str,notify=changed)
 def activeName(self):return next((i["name"] for i in self._items if i["id"]==self._active_id),"")
 @Property(str,notify=changed)
 def activeSummary(self):return next((f"{i['type']} · {i['host']}" for i in self._items if i["id"]==self._active_id),"")
 @Property("QVariantList",notify=streamsChanged)
 def streams(self):return self._streams
 @Property("QVariantList",notify=streamsChanged)
 def activeStreams(self):return [s for s in self._streams if s["device_id"]==self._active_id]
 @Property("QVariantList",notify=profilesChanged)
 def videoProfiles(self):return self._profiles
 @Slot(str,str,str,int,str,str,result=str)
 def addStream(self,device_id,name,kind,port,path,protocol):
  if not any(i["id"]==device_id for i in self._items):self.notice.emit("Пристрій для потоку не знайдено");return ""
  name=name.strip();kind=kind.strip().lower() or "main";protocol=protocol.strip().lower() or "rtsp";path=path.strip() or "/";port=max(1,min(int(port),65535))
  if not name or protocol not in ("rtsp","udp","tcp") or not path.startswith("/"):self.notice.emit("Некоректні параметри відеопотоку");return ""
  sid=uuid.uuid4().hex
  try:
   with self._connect() as db:db.execute("INSERT INTO streams(id,device_id,name,kind,protocol,port,path,video_profile_id,enabled) VALUES(?,?,?,?,?,?,?,NULL,1)",(sid,device_id,name,kind,protocol,port,path))
  except sqlite3.IntegrityError:self.notice.emit("Потік такого типу вже існує для цього пристрою");return ""
  self._load_streams();return sid
 @Slot(str,str)
 def setStreamVideoProfile(self,stream_id,profile_id):
  profile_id=profile_id.strip() or None
  if profile_id and not any(p["id"]==profile_id for p in self._profiles):self.notice.emit("Відеопрофіль не знайдено");return
  with self._connect() as db:db.execute("UPDATE streams SET video_profile_id=? WHERE id=?",(profile_id,stream_id))
  self._load_streams()
 @Slot(str)
 def removeStream(self,stream_id):
  with self._connect() as db:db.execute("DELETE FROM streams WHERE id=?",(stream_id,))
  self._load_streams()
 @Slot(str,str,str,int,int,int,int,str,str,result=str)
 def saveVideoProfile(self,profile_id,name,codec,width,height,fps,bitrate,latency_mode,notes):
  profile_id=profile_id.strip() or uuid.uuid4().hex;name=name.strip();codec=codec.strip().lower();latency_mode=latency_mode.strip().lower() or "balanced"
  if not name or codec not in ("h264","h265"):self.notice.emit("Некоректний відеопрофіль");return ""
  def nullable(v):return int(v) if int(v)>0 else None
  try:
   with self._connect() as db:db.execute("INSERT INTO video_profiles(id,name,codec,width,height,fps,bitrate_kbps,latency_mode,notes) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,codec=excluded.codec,width=excluded.width,height=excluded.height,fps=excluded.fps,bitrate_kbps=excluded.bitrate_kbps,latency_mode=excluded.latency_mode,notes=excluded.notes",(profile_id,name,codec,nullable(width),nullable(height),nullable(fps),nullable(bitrate),latency_mode,notes.strip()))
  except sqlite3.IntegrityError:self.notice.emit("Назва відеопрофілю вже використовується");return ""
  self._load_profiles();return profile_id
 @Property("QVariantList",notify=discoveryChanged)
 def discovered(self):return self._discovered
 @Property("QVariantList",notify=discoveryChanged)
 def networkInterfaces(self):return self._interfaces
 @Property(str,notify=discoveryChanged)
 def selectedInterfaceId(self):return self._selected_interface
 @Property(bool,notify=discoveryChanged)
 def scanning(self):return self._scanning
 @Property(str,notify=discoveryChanged)
 def scanStage(self):return self._stage
 @Property(int,notify=discoveryChanged)
 def scanDone(self):return self._pd
 @Property(int,notify=discoveryChanged)
 def scanTotal(self):return self._pt
 @Property(int,notify=discoveryChanged)
 def foundCount(self):return self._found
 @Property(str,notify=discoveryChanged)
 def scanStatus(self):return self._status
 @Slot()
 def refreshInterfaces(self):self._interfaces=interfaces();ids=[i["id"] for i in self._interfaces];self._selected_interface=self._selected_interface if self._selected_interface in ids else(ids[0] if ids else "");self.discoveryChanged.emit()
 @Slot(str)
 def setSelectedInterface(self,i):
  if not self._scanning and any(x["id"]==i for x in self._interfaces):self._selected_interface=i;self.discoveryChanged.emit()
 @Slot()
 def discoverOpenIPC(self):
  if self._scanning:return
  iface=next((i for i in self._interfaces if i["id"]==self._selected_interface),None)
  if not iface:self._status="Помилка";self.notice.emit("Немає вибраного IPv4 мережевого інтерфейсу");self.discoveryChanged.emit();return
  self._scanning=True;self._discovered=[];self._stage="mDNS";self._pd=self._pt=self._found=0;self._status="Сканування";self.discoveryChanged.emit();self._worker=Worker(iface);self._worker.progress.connect(self._progress);self._worker.live.connect(self._live);self._worker.done.connect(self._done);self._worker.finished.connect(self._worker_finished);self._worker.start()
 @Slot()
 def cancelDiscovery(self):
  if self._scanning and self._worker:self._status="Скасування";self.discoveryChanged.emit();self._worker.stop()
 @Slot(str,int,int,int)
 def _progress(self,s,d,t,f):self._stage,self._pd,self._pt,self._found=s,d,t,f;self.discoveryChanged.emit()
 @Slot(object)
 def _live(self,r):self._discovered=list(r);self._found=len(r);self.discoveryChanged.emit()
 @Slot(object,bool,str)
 def _done(self,r,c,e):self._discovered=list(r);self._found=len(r);self._scanning=False;self._status="Помилка" if e else("Скасовано" if c else "Завершено");self.discoveryChanged.emit();self.notice.emit((e or self._status)+f": {len(r)} знайдено")
 @Slot()
 def _worker_finished(self):
  worker=self.sender()
  if worker is self._worker:self._worker=None
  if worker:worker.deleteLater()
 @Slot(str,str,bool,result=str)
 def addDiscovered(self,host,name,confirmed):
  if not confirmed:return ""
  for i in self._items:
   if i["host"]==host:self._active_id=i["id"];self._save_active();self.changed.emit();return i["id"]
  return self.addDevice(name or "OpenIPC "+host,"Камера OpenIPC",host,80,"Мережа","OpenIPC verified")
 @Slot(str,str,str,int,str,str,result=str)
 def addDevice(self,name,device_type,host,port,connection,note):
  name,host=name.strip(),host.strip()
  if not name or not valid_host(host):self.notice.emit("Вкажіть коректні назву та IPv4/hostname без схеми URL або шляху");return ""
  port=max(1,min(int(port),65535));did=uuid.uuid4().hex
  try:
   with self._connect() as db:db.execute("INSERT INTO devices VALUES(?,?,?,?,?,?,?)",(did,name,device_type,host,port,connection,note.strip()))
  except sqlite3.IntegrityError:self.notice.emit("Пристрій з таким host і портом уже існує");return ""
  self._load();self.changed.emit();return did
 @Slot(str,str,str,int,str,result=bool)
 def updateDevice(self,did,name,host,port,note):
  name,host=name.strip(),host.strip()
  if not name or not valid_host(host):self.notice.emit("Вкажіть коректні назву та IPv4/hostname без схеми URL або шляху");return False
  try:
   with self._connect() as db:cur=db.execute("UPDATE devices SET name=?,host=?,port=?,notes=? WHERE id=?",(name,host,max(1,min(int(port),65535)),note.strip(),did))
  except sqlite3.IntegrityError:self.notice.emit("Пристрій з таким host і портом уже існує");return False
  if not cur.rowcount:return False
  self._load();self.changed.emit();return True
 @Slot(str)
 def setActive(self,did):
  if any(i["id"]==did for i in self._items):self._active_id=did;self._save_active();self.changed.emit();self.streamsChanged.emit()
 @Slot()
 def clearActive(self):
  self._active_id="";self._save_active();self.changed.emit();self.streamsChanged.emit()
 @Slot(str)
 def removeDevice(self,did):
  with self._connect() as db:db.execute("DELETE FROM devices WHERE id=?",(did,))
  if self._active_id==did:self._active_id="";self._save_active()
  self._load();self.changed.emit()
