import json,os,uuid,socket,re,time,urllib.request,ipaddress,concurrent.futures,threading,psutil
from pathlib import Path
from PySide6.QtCore import QObject,Property,Signal,Slot,QThread
from zeroconf import ServiceBrowser,ServiceListener,Zeroconf
DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';DB=DATA/'devices.json';SERVICES=('_http._tcp.local.','_rtsp._tcp.local.','_ssh._tcp.local.');WS=('239.255.255.250',3702)
def merge(f,h,n='',s='',verified=False,e=''):
 if not h:return
 x=f.setdefault(h,{'name':n or h,'host':h,'hostname':n or h,'services':[],'openipc':False,'evidence':[]})
 if n and x['name']==h:x['name']=n;x['hostname']=n
 if s and s not in x['services']:x['services'].append(s)
 if verified:x['openipc']=True
 if e and e not in x['evidence']:x['evidence'].append(e)
def interfaces():
 out=[];stats=psutil.net_if_stats()
 for name,addrs in psutil.net_if_addrs().items():
  if name in stats and not stats[name].isup:continue
  for a in addrs:
   if a.family==socket.AF_INET and a.address and not a.address.startswith('127.'):
    mask=a.netmask or '255.255.255.0'
    try:net=str(ipaddress.ip_network(f'{a.address}/{mask}',strict=False))
    except ValueError:net=str(ipaddress.ip_network(f'{a.address}/24',strict=False))
    out.append({'id':f'{name}|{a.address}','name':name,'address':a.address,'netmask':mask,'network':net,'label':f'{name} — {a.address} — {net}'})
 return out
def probe(h,cancel):
 if cancel.is_set():return h,False,[]
 ev=[];verified=False
 try:
  q=urllib.request.Request(f'<scrubbed-url-domain>',headers={'Accept':'application/json','User-Agent':'FPV-Uhyliant'})
  with urllib.request.urlopen(q,timeout=.45) as r:d=json.loads(r.read(524288).decode())
  if isinstance(d,dict) and d and any(k in d for k in ('video0','video1','system','fpv','isp','rtsp')):verified=True;ev.append('Majestic /api/v1/config.json')
 except Exception:pass
 if cancel.is_set():return h,verified,ev
 try:
  q=urllib.request.Request(f'<scrubbed-url-domain>',headers={'User-Agent':'FPV-Uhyliant'})
  with urllib.request.urlopen(q,timeout=.35) as r:b=r.read(65536).decode('utf-8','ignore').lower()
  if 'openipc' in b or 'majestic' in b:verified=True;ev.append('OpenIPC/Majestic WebUI :85')
 except Exception:pass
 return h,verified,ev
def onvif(f,cancel,bind_ip):
 for typ in ('dn:NetworkVideoTransmitter',''):
  if cancel.is_set():return
  mid=str(uuid.uuid4());types=f'<d:Types>{typ}</d:Types>' if typ else ''
  x=('<?xml version="1.0"?><e:Envelope xmlns:e="http://<scrubbed-url-domain>/2003/05/soap-envelope" xmlns:w="http://<scrubbed-url-domain>/ws/2004/08/addressing" xmlns:d="http://<scrubbed-url-domain>/ws/2005/04/discovery" xmlns:dn="http://<scrubbed-url-domain>/ver10/network/wsdl"><e:Header><w:MessageID>uuid:'+mid+'</w:MessageID><w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To><w:Action>http://<scrubbed-url-domain>/ws/2005/04/discovery/Probe</w:Action></e:Header><e:Body><d:Probe>'+types+'</d:Probe></e:Body></e:Envelope>').encode();s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
  try:
   s.bind((bind_ip,0));s.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_IF,socket.inet_aton(bind_ip));s.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,2);s.settimeout(.2)
   for _ in range(2):s.sendto(x,WS)
   end=time.monotonic()+2.5
   while time.monotonic()<end and not cancel.is_set():
    try:d,a=s.recvfrom(65535)
    except socket.timeout:continue
    t=d.decode('utf-8','ignore');h=a[0];hint='openipc' in t.lower();merge(f,h,'ONVIF '+h,'ONVIF',False,'ONVIF OpenIPC hint' if hint else 'ONVIF WS-Discovery')
  finally:s.close()
class Worker(QThread):
 done=Signal(object,bool,str);progress=Signal(str,int,int,int);live=Signal(object)
 def __init__(self,iface):super().__init__();self.cancel=threading.Event();self.iface=iface
 def stop(self):self.cancel.set();self.requestInterruption()
 def emitp(self,s,d=0,t=0,f=0):self.progress.emit(s,d,t,f)
 def run(self):
  found={};w=self;bind_ip=self.iface['address'];network=ipaddress.ip_network(self.iface['network'],strict=False)
  try:
   self.emitp('mDNS',0,0,0)
   class L(ServiceListener):
    def add_service(self,z,t,n):
     if w.cancel.is_set():return
     try:
      i=z.get_service_info(t,n,timeout=800)
      if not i:return
      p={k.decode(errors='ignore').lower():v.decode(errors='ignore') for k,v in i.properties.items()};server=(i.server or '').rstrip('.');vendor=p.get('vendor','').strip().lower();verified=vendor=='openipc';hint='openipc' in n.lower() or 'openipc' in server.lower();e='mDNS vendor=OpenIPC' if verified else ('mDNS OpenIPC name hint' if hint else 'mDNS')
      for h in i.parsed_addresses():
       try:
        if ipaddress.ip_address(h) not in network:continue
       except ValueError:continue
       merge(found,h,server or n.split('.')[0],t,verified,e)
      w.live.emit(list(found.values()));w.emitp('mDNS',0,0,len(found))
     except Exception:pass
    def update_service(self,z,t,n):self.add_service(z,t,n)
    def remove_service(self,z,t,n):pass
   z=Zeroconf(interfaces=[bind_ip]);listener=L();bs=[ServiceBrowser(z,t,listener) for t in SERVICES];end=time.monotonic()+3.5
   while time.monotonic()<end and not self.cancel.is_set():self.msleep(100)
   for b in bs:b.cancel()
   z.close()
   if not self.cancel.is_set():self.emitp('ONVIF',0,0,len(found));onvif(found,self.cancel,bind_ip);self.live.emit(list(found.values()))
   if not self.cancel.is_set():
    targets=list(found);self.emitp('fingerprint',0,len(targets),len(found))
    for i,h in enumerate(targets,1):
     if self.cancel.is_set():break
     _,verified,ev=probe(h,self.cancel)
     if verified:
      merge(found,h,s='Majestic/OpenIPC fingerprint',verified=True,e=ev[0])
      for e in ev[1:]:merge(found,h,e=e)
     self.emitp('fingerprint',i,len(targets),len(found));self.live.emit(list(found.values()))
   if not self.cancel.is_set():
    n24=ipaddress.ip_network(bind_ip+'/24',strict=False);hosts=[str(h) for h in n24.hosts()];total=len(hosts);done=0;self.emitp('/24',0,total,len(found));ex=concurrent.futures.ThreadPoolExecutor(max_workers=32);pending={ex.submit(probe,h,self.cancel) for h in hosts}
    try:
     while pending and not self.cancel.is_set():
      finished,pending=concurrent.futures.wait(pending,timeout=.1,return_when=concurrent.futures.FIRST_COMPLETED)
      for fut in finished:
       done+=1;h,verified,ev=fut.result()
       if verified:
        merge(found,h,'OpenIPC '+h,'/24 fingerprint',True,ev[0])
        for e in ev[1:]:merge(found,h,e=e)
       self.emitp('/24',done,total,len(found))
      if finished:self.live.emit(list(found.values()))
    finally:
     if self.cancel.is_set():
      for fut in pending:fut.cancel()
     ex.shutdown(wait=not self.cancel.is_set(),cancel_futures=True)
   r=list(found.values())
   for x in r:x['confidence']='OpenIPC підтверджено' if x['openipc'] else 'Кандидат, не підтверджено'
   r.sort(key=lambda x:(not x['openipc'],x['host']));self.done.emit(r,self.cancel.is_set(),'')
  except Exception as e:self.done.emit(list(found.values()),False,str(e))
class Devices(QObject):
 changed=Signal();notice=Signal(str);discoveryChanged=Signal()
 def __init__(self):
  super().__init__();DATA.mkdir(parents=True,exist_ok=True);self._items=[];self._active_id='';self._discovered=[];self._scanning=False;self._worker=None;self._stage='Готово';self._pd=0;self._pt=0;self._found=0;self._status='Готово';self._interfaces=[];self._selected_interface='';self._load();self.refreshInterfaces()
 def _load(self):
  try:r=json.loads(DB.read_text(encoding='utf-8')) if DB.exists() else {};self._items=r.get('devices',[]);self._active_id=r.get('activeDeviceId','')
  except Exception:self._items=[];self._active_id=''
 def _save(self):p=DB.with_suffix('.tmp');p.write_text(json.dumps({'schema':1,'activeDeviceId':self._active_id,'devices':self._items},ensure_ascii=False,indent=2),encoding='utf-8');os.replace(p,DB)
 def _pub(self,x):return {**x,'active':x.get('id')==self._active_id}
 @Property('QVariantList',notify=changed)
 def items(self):return [self._pub(x) for x in self._items]
 @Property(int,notify=changed)
 def count(self):return len(self._items)
 @Property(str,notify=changed)
 def activeName(self):return next((x.get('name','') for x in self._items if x.get('id')==self._active_id),'')
 @Property(str,notify=changed)
 def activeSummary(self):return next((f"{x.get('type','')} · {x.get('host','')}" for x in self._items if x.get('id')==self._active_id),'')
 @Property('QVariantList',notify=discoveryChanged)
 def discovered(self):return self._discovered
 @Property('QVariantList',notify=discoveryChanged)
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
 def refreshInterfaces(self):
  self._interfaces=interfaces();ids=[x['id'] for x in self._interfaces]
  if self._selected_interface not in ids:self._selected_interface=ids[0] if ids else ''
  self.discoveryChanged.emit()
 @Slot(str)
 def setSelectedInterface(self,i):
  if not self._scanning and any(x['id']==i for x in self._interfaces):self._selected_interface=i;self.discoveryChanged.emit()
 @Slot()
 def discoverOpenIPC(self):
  if self._scanning:return
  iface=next((x for x in self._interfaces if x['id']==self._selected_interface),None)
  if not iface:self._status='Помилка';self.notice.emit('Немає вибраного IPv4 мережевого інтерфейсу');self.discoveryChanged.emit();return
  self._scanning=True;self._discovered=[];self._stage='mDNS';self._pd=0;self._pt=0;self._found=0;self._status='Сканування';self.discoveryChanged.emit();self._worker=Worker(iface);self._worker.progress.connect(self._progress);self._worker.live.connect(self._live);self._worker.done.connect(self._done);self._worker.start()
 @Slot()
 def cancelDiscovery(self):
  if self._scanning and self._worker:self._status='Скасування';self.discoveryChanged.emit();self._worker.stop()
 @Slot(str,int,int,int)
 def _progress(self,s,d,t,f):self._stage=s;self._pd=d;self._pt=t;self._found=f;self.discoveryChanged.emit()
 @Slot(object)
 def _live(self,r):self._discovered=list(r);self._found=len(r);self.discoveryChanged.emit()
 @Slot(object,bool,str)
 def _done(self,r,c,e):self._discovered=list(r);self._found=len(r);self._scanning=False;self._worker=None;self._status='Помилка' if e else ('Скасовано' if c else 'Завершено');self.discoveryChanged.emit();self.notice.emit((e or self._status)+f': {len(r)} знайдено')
 @Slot(str,str,bool,result=str)
 def addDiscovered(self,h,n,confirmed):
  if not confirmed:return ''
  for x in self._items:
   if x.get('host')==h:self._active_id=x['id'];self._save();self.changed.emit();return x['id']
  return self.addDevice(n or 'OpenIPC '+h,'Камера OpenIPC',h,80,'Мережа','OpenIPC verified')
 @Slot(str,str,str,int,str,str,result=str)
 def addDevice(self,n,t,h,p,c,note):
  if not n.strip():return ''
  i=uuid.uuid4().hex;self._items.append({'id':i,'name':n.strip(),'type':t,'host':h.strip(),'port':max(0,min(int(p),65535)),'connection':c,'notes':note.strip()});self._active_id=self._active_id or i;self._save();self.changed.emit();return i
 @Slot(str,str,str,int,str,result=bool)
 def updateDevice(self,i,n,h,p,note):
  for x in self._items:
   if x.get('id')==i:x['name']=n.strip() or x['name'];x['host']=h.strip();x['port']=max(0,min(int(p),65535));x['notes']=note.strip();self._save();self.changed.emit();return True
  return False
 @Slot(str)
 def setActive(self,i):
  if any(x.get('id')==i for x in self._items):self._active_id=i;self._save();self.changed.emit()
 @Slot(str)
 def removeDevice(self,i):
  self._items=[x for x in self._items if x.get('id')!=i];self._active_id=self._items[0]['id'] if self._active_id==i and self._items else ('' if self._active_id==i else self._active_id);self._save();self.changed.emit()
