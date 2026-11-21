import ipaddress
import threading
from PySide6.QtCore import Property, QThread, Signal, Slot
from devices import Devices as LegacyDevices, interfaces
from openipc_device import normalize_openipc_identity
from route_discovery import discover_targets, fingerprint, plan_targets, system_routes


class DiscoveryWorker(QThread):
    progress = Signal(str, int, int, int); live = Signal(object); done = Signal(object, bool, str)
    def __init__(self, targets): super().__init__(); self.targets=targets; self.cancel=threading.Event()
    def stop(self): self.cancel.set(); self.requestInterruption()
    def run(self):
        try:
            self.progress.emit("Перевірка маршрутів",0,len(self.targets),0)
            def update(done,total,found): self.progress.emit("Пошук камер",done,total,found)
            items=discover_targets(self.targets,self.cancel,update); self.live.emit(items); self.done.emit(items,self.cancel.is_set(),"")
        except Exception as exc: self.done.emit([],self.cancel.is_set(),str(exc))


class ManualWorker(QThread):
    done=Signal(object,str)
    def __init__(self,host): super().__init__(); self.host=host; self.cancel=threading.Event()
    def run(self):
        try:self.done.emit(fingerprint(self.host,self.cancel),"")
        except Exception as exc:self.done.emit({},str(exc))


class Devices(LegacyDevices):
    manualChanged=Signal()
    def __init__(self):
        super().__init__(); self._manual_busy=False; self._manual_result={}; self._manual_error=""; self._manual_worker=None
        self._init_discovery_history()

    def _init_discovery_history(self):
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS discovery_history(host TEXT PRIMARY KEY,last_seen INTEGER NOT NULL DEFAULT 0,openipc INTEGER NOT NULL DEFAULT 0)")

    def _remember_host(self,host,openipc=False):
        if not host:return
        try:
            address=str(ipaddress.ip_address(host))
        except ValueError:return
        with self._connect() as db:
            db.execute("INSERT INTO discovery_history(host,last_seen,openipc) VALUES(?,strftime('%s','now'),?) ON CONFLICT(host) DO UPDATE SET last_seen=excluded.last_seen,openipc=MAX(discovery_history.openipc,excluded.openipc)",(address,int(bool(openipc))))

    def _known_hosts(self):
        hosts={item.get("host","") for item in self._items}
        with self._connect() as db: hosts.update(row[0] for row in db.execute("SELECT host FROM discovery_history ORDER BY last_seen DESC"))
        return sorted(hosts)

    @Property(bool,notify=manualChanged)
    def manualBusy(self):return self._manual_busy
    @Property("QVariantMap",notify=manualChanged)
    def manualResult(self):return self._manual_result
    @Property(str,notify=manualChanged)
    def manualError(self):return self._manual_error
    @Property(str,notify=LegacyDevices.discoveryChanged)
    def scanStage(self):return self._stage
    @Property(str,notify=LegacyDevices.discoveryChanged)
    def scanStatus(self):return self._status
    @Property(int,notify=LegacyDevices.discoveryChanged)
    def scanDone(self):return self._pd
    @Property(int,notify=LegacyDevices.discoveryChanged)
    def scanTotal(self):return self._pt

    @Slot()
    def discoverOpenIPC(self):
        if self._scanning:return
        targets=plan_targets(interfaces(),system_routes(),self._known_hosts())
        self._discovered=[]; self._scanning=True; self._stage="Планування"; self._pd=0; self._pt=len(targets); self._found=0; self._status="Скануються лише безпечні приватні маршрути"; self.discoveryChanged.emit()
        worker=DiscoveryWorker(targets); self._worker=worker; worker.progress.connect(self._on_progress); worker.live.connect(self._on_live); worker.done.connect(self._on_done); worker.start()

    @Slot()
    def cancelDiscovery(self):
        if self._worker:self._worker.stop()
    def _on_progress(self,stage,done,total,found):self._stage=stage;self._pd=done;self._pt=total;self._found=found;self.discoveryChanged.emit()
    def _on_live(self,items):self._discovered=items;self._found=len(items);self.discoveryChanged.emit()
    def _on_done(self,items,cancelled,error):
        for item in items:self._remember_host(item.get("host",""),item.get("openipc",False))
        self._discovered=items;self._scanning=False;self._worker=None;self._stage="Скасовано" if cancelled else ("Помилка" if error else "Готово");self._status=error or ("Пошук скасовано" if cancelled else "Пошук завершено");self._pd=self._pt;self._found=len(items);self.discoveryChanged.emit()

    @Slot(str)
    def inspectManualIp(self,value):
        if self._manual_busy:return
        try:
            address=ipaddress.ip_address(value.strip())
            if address.version!=4 or address.is_unspecified or address.is_multicast or address.is_loopback:raise ValueError
        except ValueError:
            self._manual_error="Вкажіть коректну IPv4-адресу";self._manual_result={};self.manualChanged.emit();return
        self._remember_host(str(address),False)
        self._manual_busy=True;self._manual_error="";self._manual_result={};self.manualChanged.emit();worker=ManualWorker(str(address));self._manual_worker=worker;worker.done.connect(self._on_manual_done);worker.start()
    def _on_manual_done(self,result,error):
        self._manual_busy=False;self._manual_worker=None;self._manual_result=result if result.get("camera") else {};self._manual_error=error or ("На цій адресі не знайдено доступної камери" if not self._manual_result else "")
        if self._manual_result:self._remember_host(result.get("host",""),result.get("openipc",False))
        self.manualChanged.emit()

    @Slot(str,str,bool,result=str)
    def addDiscovered(self,host,name,verified):
        candidate=next((x for x in self._discovered if x.get("host")==host),None)
        if not candidate and self._manual_result.get("host")==host:candidate=self._manual_result
        identity=normalize_openipc_identity(candidate.get("identity",{}),candidate.get("evidence",[])) if candidate else normalize_openipc_identity()
        if not candidate or not candidate.get("openipc") or not candidate.get("identityVerified") or not identity.get("verified"):return ""
        self._remember_host(host,True)
        existing=next((x for x in self._items if x.get("host")==host),None)
        if existing:return existing["id"]
        did=self.addDevice(name or "OpenIPC "+host,"OpenIPC",host,80,"Network","")
        if not did:return ""
        self._save_identity(did,identity)
        for stream in candidate.get("streams",[]):self.addStream(did,stream.get("name","Відео"),stream.get("name","main"),int(stream.get("port",554)),stream.get("path","/"),stream.get("protocol","rtsp"))
        self._load();self.changed.emit();return did

    @Slot(str,str,str,int,str,result=bool)
    def updateDevice(self,did,name,host,port,notes):
        name=name.strip();host=host.strip();from devices import valid_host
        if not name or not valid_host(host):return False
        try:
            with self._connect() as db:db.execute("UPDATE devices SET name=?,host=?,port=?,notes=? WHERE id=?",(name,host,max(1,min(int(port),65535)),notes.strip(),did))
        except Exception:return False
        self._remember_host(host,False);self._load();self.changed.emit();return True
