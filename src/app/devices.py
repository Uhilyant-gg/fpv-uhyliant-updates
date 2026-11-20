import json,os,uuid,socket,re,time,urllib.request,ipaddress,concurrent.futures
from pathlib import Path
from PySide6.QtCore import QObject,Property,Signal,Slot,QThread
from zeroconf import ServiceBrowser,ServiceListener,Zeroconf
DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';DB=DATA/'devices.json';SERVICES=('_http._tcp.local.','_rtsp._tcp.local.','_ssh._tcp.local.');WS=('239.255.255.250',3702)
def merge(f,h,n='',s='',o=False,e=''):
 if not h:return
 x=f.setdefault(h,{'name':n or h,'host':h,'services':[],'openipc':False,'evidence':[]})
 if n and x['name']==h:x['name']=n
 if s and s not in x['services']:x['services'].append(s)
 x['openipc']|=o
 if e and e not in x['evidence']:x['evidence'].append(e)
def local_ipv4():
 out=set()
 try:
  for a in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):
   ip=a[4][0]
   if not ip.startswith('127.'):out.add(ip)
 except OSError:pass
 try:
  s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('1.1.1.1',53));out.add(s.getsockname()[0]);s.close()
 except OSError:pass
 return sorted(out)
def probe(h):
 evidence=[];ok=False
 try:
  q=urllib.request.Request(f'<scrubbed-url-domain>',headers={'Accept':'application/json','User-Agent':'FPV-Uhyliant'})
  with urllib.request.urlopen(q,timeout=.45) as r:d=json.loads(r.read(524288).decode())
  if isinstance(d,dict) and d and any(k in d for k in ('video0','video1','system','fpv','isp','rtsp')):ok=True;evidence.append('Majestic /api/v1/config.json')
 except Exception:pass
 try:
  q=urllib.request.Request(f'<scrubbed-url-domain>',headers={'User-Agent':'FPV-Uhyliant'})
  with urllib.request.urlopen(q,timeout=.35) as r:b=r.read(65536).decode('utf-8','ignore').lower()
  if 'openipc' in b or 'majestic' in b:ok=True;evidence.append('OpenIPC WebUI :85')
 except Exception:pass
 return h,ok,evidence
def scan24(f):
 nets={ipaddress.ip_network(ip+'/24',strict=False) for ip in local_ipv4()}
 hosts=[str(h) for n in nets for h in n.hosts()]
 with concurrent.futures.ThreadPoolExecutor(max_workers=32) as ex:
  for h,ok,ev in ex.map(probe,hosts):
   if ok:
    merge(f,h,'OpenIPC '+h,'Local /24 scan',True,ev[0])
    for e in ev[1:]:merge(f,h,e=e)
def fingerprint(f):
 for h in list(f):
  _,ok,ev=probe(h)
  if ok:
   merge(f,h,s='Majestic HTTP',o=True,e=ev[0])
   for e in ev[1:]:merge(f,h,e=e)
def onvif(f):
 for typ in ('dn:NetworkVideoTransmitter',''):
  mid=str(uuid.uuid4());types=f'<d:Types>{typ}</d:Types>' if typ else ''
  x=('<?xml version="1.0"?><e:Envelope xmlns:e="http://<scrubbed-url-domain>/2003/05/soap-envelope" xmlns:w="http://<scrubbed-url-domain>/ws/2004/08/addressing" xmlns:d="http://<scrubbed-url-domain>/ws/2005/04/discovery" xmlns:dn="http://<scrubbed-url-domain>/ver10/network/wsdl"><e:Header><w:MessageID>uuid:'+mid+'</w:MessageID><w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To><w:Action>http://<scrubbed-url-domain>/ws/2005/04/discovery/Probe</w:Action></e:Header><e:Body><d:Probe>'+types+'</d:Probe></e:Body></e:Envelope>').encode();s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
  try:
   s.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,2);s.settimeout(.3)
   for _ in range(2):s.sendto(x,WS)
   end=time.monotonic()+2.5
   while time.monotonic()<end:
    try:d,a=s.recvfrom(65535)
    except socket.timeout:continue
    t=d.decode('utf-8','ignore');h=a[0];m=re.search(r'<(?:\w+:)?XAddrs[^>]*>.*?https?://([^/:\s]+)',t,re.I|re.S);h=m.group(1) if m else h;o='openipc' in t.lower();merge(f,h,'ONVIF '+h,'ONVIF WS-Discovery',o,'ONVIF OpenIPC marker' if o else 'ONVIF')
  finally:s.close()
class Worker(QThread):
 done=Signal(object)
 def run(self):
  f={}
  class L(ServiceListener):
   def add_service(self,z,t,n):
    try:
     i=z.get_service_info(t,n,timeout=1000)
     if not i:return
     p={k.decode(errors='ignore').lower():v.decode(errors='ignore') for k,v in i.properties.items()};server=(i.server or '').rstrip('.');o=p.get('vendor','').lower()=='openipc' or 'openipc' in n.lower()
     for h in i.parsed_addresses():merge(f,h,server or n.split('.')[0],t,o,'mDNS vendor=OpenIPC' if o else 'mDNS')
    except Exception:pass
   def update_service(self,z,t,n):self.add_service(z,t,n)
   def remove_service(self,z,t,n):pass
  z=Zeroconf();bs=[ServiceBrowser(z,t,L()) for t in SERVICES];self.msleep(3500)
  for b in bs:b.cancel()
  z.close();onvif(f);fingerprint(f);scan24(f)
  r=[]
  for x in f.values():x['confidence']='OpenIPC підтверджено' if x['openipc'] else ('ONVIF камера' if 'ONVIF WS-Discovery' in x['services'] else 'Мережева камера');r.append(x)
  r.sort(key=lambda x:(not x['openipc'],x['host']));self.done.emit(r)
class Devices(QObject):
 changed=Signal();notice=Signal(str);discoveryChanged=Signal()
 def __init__(self):super().__init__();DATA.mkdir(parents=True,exist_ok=True);self._items=[];self._active_id='';self._discovered=[];self._scanning=False;self._worker=None;self._load()
 def _load(self):
  try:r=json.loads(DB.read_text(encoding='utf-8')) if DB.exists() else {};self._items=r.get('devices',[]);self._active_id=r.get('activeDeviceId','')
  except Exception:self._items=[];self._active_id=''
 def _save(self):
  p=DB.with_suffix('.tmp');p.write_text(json.dumps({'schema':1,'activeDeviceId':self._active_id,'devices':self._items},ensure_ascii=False,indent=2),encoding='utf-8');os.replace(p,DB)
 def _pub(self,x):return {**x,'active':x.get('id')==self._active_id}
 @Property('QVariantList',notify=changed)
 def items(self):return [self._pub(x) for x in self._items]
 @Property(int,notify=changed)
 def count(self):return len(self._items)
 @Property(str,notify=changed)
 def activeId(self):return self._active_id
 @Property(str,notify=changed)
 def activeName(self):return next((x.get('name','') for x in self._items if x.get('id')==self._active_id),'')
 @Property(str,notify=changed)
 def activeSummary(self):return next((f"{x.get('type','')} · {x.get('host','')}" for x in self._items if x.get('id')==self._active_id),'')
 @Property('QVariantList',notify=discoveryChanged)
 def discovered(self):return self._discovered
 @Property(bool,notify=discoveryChanged)
 def scanning(self):return self._scanning
 @Slot()
 def discoverOpenIPC(self):
  if self._scanning:return
  self._scanning=True;self._discovered=[];self.discoveryChanged.emit();self._worker=Worker();self._worker.done.connect(self._done);self._worker.start()
 @Slot(object)
 def _done(self,r):self._discovered=list(r);self._scanning=False;self.discoveryChanged.emit();self.notice.emit(f'Повний пошук завершено: {len(r)} знайдено')
 @Slot(str,str,result=str)
 def addDiscovered(self,h,n):
  for x in self._items:
   if x.get('host')==h:self._active_id=x['id'];self._save();self.changed.emit();return x['id']
  return self.addDevice(n or 'OpenIPC '+h,'Камера OpenIPC',h,80,'Мережа','Додано через network discovery')
 @Slot(str,str,str,int,str,str,result=str)
 def addDevice(self,n,t,h,p,c,note):
  if not n.strip():return ''
  i=uuid.uuid4().hex;self._items.append({'id':i,'name':n.strip(),'type':t,'host':h.strip(),'port':max(0,min(int(p),65535)),'connection':c,'notes':note.strip()});self._active_id=self._active_id or i;self._save();self.changed.emit();return i
 @Slot(str)
 def setActive(self,i):
  if any(x.get('id')==i for x in self._items):self._active_id=i;self._save();self.changed.emit()
 @Slot(str)
 def removeDevice(self,i):
  self._items=[x for x in self._items if x.get('id')!=i];self._active_id=self._items[0]['id'] if self._active_id==i and self._items else ('' if self._active_id==i else self._active_id);self._save();self.changed.emit()
