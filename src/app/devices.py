import json, os, uuid
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot, QThread
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

DATA = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'FPV-Uhyliant'
DB = DATA / 'devices.json'
SERVICES = ('_http._tcp.local.', '_rtsp._tcp.local.', '_ssh._tcp.local.')

class DiscoveryWorker(QThread):
    done = Signal(object)
    def run(self):
        found = {}
        class Listener(ServiceListener):
            def add_service(self, zc, service_type, name):
                try:
                    info = zc.get_service_info(service_type, name, timeout=1200)
                    if not info: return
                    props = {k.decode(errors='ignore').lower(): v.decode(errors='ignore') for k,v in info.properties.items()}
                    vendor = props.get('vendor','').lower()
                    server = (info.server or '').rstrip('.')
                    addresses = info.parsed_addresses()
                    for host in addresses:
                        key = host
                        item = found.setdefault(key, {'name': server or name.split('.')[0], 'host': host, 'services': [], 'openipc': False, 'evidence': []})
                        if service_type not in item['services']: item['services'].append(service_type)
                        if vendor == 'openipc': item['openipc'] = True; item['evidence'].append('mDNS vendor=OpenIPC')
                        if 'openipc' in name.lower() or 'openipc' in server.lower(): item['openipc'] = True; item['evidence'].append('mDNS name')
                except Exception: pass
            def update_service(self, zc, service_type, name): self.add_service(zc, service_type, name)
            def remove_service(self, zc, service_type, name): pass
        zc = Zeroconf(); listener = Listener(); browsers=[]
        try:
            for service in SERVICES: browsers.append(ServiceBrowser(zc, service, listener))
            self.msleep(4500)
        finally:
            for b in browsers:
                try: b.cancel()
                except Exception: pass
            zc.close()
        results=[]
        for item in found.values():
            # Keep explicit OpenIPC matches first; generic RTSP/HTTP devices are shown as candidates.
            item['confidence'] = 'OpenIPC' if item['openipc'] else 'Мережева камера'
            results.append(item)
        results.sort(key=lambda x: (not x['openipc'], x['host']))
        self.done.emit(results)

class Devices(QObject):
    changed = Signal(); notice = Signal(str); discoveryChanged = Signal()
    def __init__(self):
        super().__init__(); DATA.mkdir(parents=True, exist_ok=True); self._items=[]; self._active_id=''; self._discovered=[]; self._scanning=False; self._worker=None; self._load()
    def _load(self):
        try:
            raw=json.loads(DB.read_text(encoding='utf-8')) if DB.exists() else {}; self._items=raw.get('devices',[]) if isinstance(raw,dict) else []; self._active_id=raw.get('activeDeviceId','') if isinstance(raw,dict) else ''
            if self._active_id and not any(x.get('id')==self._active_id for x in self._items): self._active_id=''
        except (OSError,ValueError,TypeError): self._items=[];self._active_id=''
    def _save(self):
        tmp=DB.with_suffix('.tmp');tmp.write_text(json.dumps({'schema':1,'activeDeviceId':self._active_id,'devices':self._items},ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,DB)
    def _public(self,item):
        return {'id':item.get('id',''),'name':item.get('name',''),'type':item.get('type',''),'host':item.get('host',''),'port':item.get('port',0),'connection':item.get('connection',''),'notes':item.get('notes',''),'active':item.get('id')==self._active_id}
    @Property('QVariantList',notify=changed)
    def items(self): return [self._public(x) for x in self._items]
    @Property(int,notify=changed)
    def count(self): return len(self._items)
    @Property(str,notify=changed)
    def activeId(self): return self._active_id
    @Property(str,notify=changed)
    def activeName(self):
        return next((x.get('name','') for x in self._items if x.get('id')==self._active_id),'')
    @Property(str,notify=changed)
    def activeSummary(self):
        for x in self._items:
            if x.get('id')==self._active_id:
                return f"{x.get('type','')} · {x.get('host','')}" if x.get('host') else x.get('type','')
        return ''
    @Property('QVariantList',notify=discoveryChanged)
    def discovered(self): return self._discovered
    @Property(bool,notify=discoveryChanged)
    def scanning(self): return self._scanning
    @Slot()
    def discoverOpenIPC(self):
        if self._scanning:return
        self._scanning=True;self._discovered=[];self.discoveryChanged.emit();self._worker=DiscoveryWorker();self._worker.done.connect(self._discoveryDone);self._worker.start()
    @Slot(object)
    def _discoveryDone(self,results):
        self._discovered=list(results);self._scanning=False;self.discoveryChanged.emit();self.notice.emit(f'Мережеве сканування завершено: {len(self._discovered)} знайдено')
    @Slot(str,str,result=str)
    def addDiscovered(self,host,name):
        for x in self._items:
            if x.get('host')==host and x.get('type')=='Камера OpenIPC': self._active_id=x['id'];self._save();self.changed.emit();return x['id']
        return self.addDevice(name or f'OpenIPC {host}','Камера OpenIPC',host,80,'Мережа','Додано через mDNS discovery')
    @Slot(str,str,str,int,str,str,result=str)
    def addDevice(self,name,device_type,host,port,connection,notes):
        name=name.strip();host=host.strip()
        if not name:self.notice.emit('Вкажіть назву пристрою');return ''
        if device_type not in ('Камера OpenIPC','Політний контролер','Борт'):self.notice.emit('Невідомий тип пристрою');return ''
        if connection not in ('Мережа','Serial/COM','Комбінований'):self.notice.emit('Невідомий тип підключення');return ''
        device_id=uuid.uuid4().hex;self._items.append({'id':device_id,'name':name,'type':device_type,'host':host,'port':max(0,min(int(port),65535)),'connection':connection,'notes':notes.strip()})
        if not self._active_id:self._active_id=device_id
        self._save();self.changed.emit();self.notice.emit('Пристрій збережено');return device_id
    @Slot(str)
    def setActive(self,device_id):
        if any(x.get('id')==device_id for x in self._items):self._active_id=device_id;self._save();self.changed.emit()
    @Slot(str)
    def removeDevice(self,device_id):
        before=len(self._items);self._items=[x for x in self._items if x.get('id')!=device_id]
        if len(self._items)==before:return
        if self._active_id==device_id:self._active_id=self._items[0]['id'] if self._items else ''
        self._save();self.changed.emit();self.notice.emit('Пристрій видалено')
