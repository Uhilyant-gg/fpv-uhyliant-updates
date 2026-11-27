import ipaddress
import threading
from PySide6.QtCore import Property, QThread, Signal, Slot
from devices import Devices as LegacyDevices, interfaces
from openipc_device import normalize_openipc_identity
from route_discovery import discover_targets, fingerprint, plan_targets, system_routes

DISCOVERY_ERROR_MESSAGE="Не вдалося завершити пошук камер. Перевірте мережу та спробуйте ще раз."
MANUAL_CHECK_ERROR_MESSAGE="Не вдалося перевірити камеру. Перевірте її адресу, живлення та мережеве з’єднання."

def _safe_private_host(value):
    try:address=ipaddress.ip_address(str(value).strip())
    except ValueError:return ""
    if address.version!=4 or not address.is_private or address.is_unspecified or address.is_multicast or address.is_loopback or address.is_link_local:return ""
    return str(address)

class DiscoveryWorker(QThread):
    progress=Signal(str,int,int,int);live=Signal(object);done=Signal(object,bool,str)
    def __init__(self,targets):super().__init__();self.targets=targets;self.cancel=threading.Event()
    def stop(self):self.cancel.set();self.requestInterruption()
    def run(self):
        try:
            self.progress.emit("Перевірка маршрутів",0,len(self.targets),0)
            def update(done,total,found):self.progress.emit("Пошук камер",done,total,found)
            items=discover_targets(self.targets,self.cancel,update);self.live.emit(items);self.done.emit(items,self.cancel.is_set(),"")
        except Exception:self.done.emit([],self.cancel.is_set(),"discovery-failed")

class ManualWorker(QThread):
    done=Signal(object,str)
    def __init__(self,host):super().__init__();self.host=host;self.cancel=threading.Event()
    def run(self):
        try:self.done.emit(fingerprint(self.host,self.cancel),"")
        except Exception:self.done.emit({},"inspection-failed")

class Devices(LegacyDevices):
    manualChanged=Signal()
    scanStateChanged=Signal()
    def __init__(self):
        super().__init__();self._manual_busy=False;self._manual_result={};self._manual_error="";self._manual_status="idle";self._manual_message="";self._manual_worker=None;self._manual_requested_host=""
        self.discoveryChanged.connect(self.scanStateChanged)
        self._init_discovery_history()
    def _init_discovery_history(self):
        with self._connect() as db:db.execute("CREATE TABLE IF NOT EXISTS discovery_history(host TEXT PRIMARY KEY,last_seen INTEGER NOT NULL DEFAULT 0,openipc INTEGER NOT NULL DEFAULT 0)")
    def _remember_host(self,host,openipc=False):
        address=_safe_private_host(host)
        if not address:return
        with self._connect() as db:db.execute("INSERT INTO discovery_history(host,last_seen,openipc) VALUES(?,strftime('%s','now'),?) ON CONFLICT(host) DO UPDATE SET last_seen=excluded.last_seen,openipc=MAX(discovery_history.openipc,excluded.openipc)",(address,int(bool(openipc))))
    def _known_hosts(self):
        hosts={host for item in self._items if (host:=_safe_private_host(item.get("host","")))}
        with self._connect() as db:
            for row in db.execute("SELECT host FROM discovery_history ORDER BY last_seen DESC"):
                host=_safe_private_host(row[0])
                if host:hosts.add(host)
        return sorted(hosts)
    def _set_manual(self,status,message="",error=""):
        self._manual_status=status;self._manual_message=message;self._manual_error=error;self.manualChanged.emit()
    @Property(bool,notify=manualChanged)
    def manualBusy(self):return self._manual_busy
    @Property("QVariantMap",notify=manualChanged)
    def manualResult(self):return self._manual_result
    @Property(str,notify=manualChanged)
    def manualError(self):return self._manual_error
    @Property(str,notify=manualChanged)
    def manualStatus(self):return self._manual_status
    @Property(str,notify=manualChanged)
    def manualMessage(self):return self._manual_message
    @Property(str,notify=scanStateChanged)
    def scanStage(self):return self._stage
    @Property(str,notify=scanStateChanged)
    def scanStatus(self):return self._status
    @Property(int,notify=scanStateChanged)
    def scanDone(self):return self._pd
    @Property(int,notify=scanStateChanged)
    def scanTotal(self):return self._pt
    @Slot()
    def discoverOpenIPC(self):
        if self._scanning:return
        targets=plan_targets(interfaces(),system_routes(),self._known_hosts())
        self._discovered=[];self._scanning=True;self._stage="Планування";self._pd=0;self._pt=len(targets);self._found=0;self._status="Скануються лише безпечні приватні маршрути";self.discoveryChanged.emit()
        worker=DiscoveryWorker(targets);self._worker=worker;worker.progress.connect(self._on_progress);worker.live.connect(self._on_live);worker.done.connect(self._on_done);worker.start()
    @Slot()
    def cancelDiscovery(self):
        if self._worker:self._worker.stop()
    def _on_progress(self,stage,done,total,found):self._stage=stage;self._pd=done;self._pt=total;self._found=found;self.discoveryChanged.emit()
    def _on_live(self,items):self._discovered=items;self._found=len(items);self.discoveryChanged.emit()
    def _on_done(self,items,cancelled,error):
        for item in items:self._remember_host(item.get("host",""),item.get("openipc",False))
        self._discovered=items;self._scanning=False;self._worker=None;self._stage="Скасовано" if cancelled else ("Помилка" if error else "Готово");self._status=DISCOVERY_ERROR_MESSAGE if error else ("Пошук скасовано" if cancelled else "Пошук завершено");self._pd=self._pt;self._found=len(items);self.discoveryChanged.emit()
    @Slot(str)
    def invalidateManualIp(self,value):
        address=_safe_private_host(value)
        current=_safe_private_host(self._manual_result.get("host","")) if self._manual_result else ""
        if self._manual_status in ("verified","added","candidate","auth-required","error") and (not address or address!=current):
            self._manual_result={};self._manual_requested_host="";self._set_manual("idle","","")
    @Slot(str)
    def inspectManualIp(self,value):
        if self._manual_busy:return
        address=_safe_private_host(value)
        self._manual_result={};self._manual_requested_host=address
        if not address:self._set_manual("error","","Вкажіть коректну приватну IPv4-адресу");return
        self._remember_host(address,False);self._manual_busy=True;self._manual_status="checking";self._manual_message="Перевіряємо камеру…";self._manual_error="";self.manualChanged.emit()
        worker=ManualWorker(address);self._manual_worker=worker;worker.done.connect(self._on_manual_done);worker.start()
    def _on_manual_done(self,result,error):
        requested=self._manual_requested_host
        self._manual_busy=False;self._manual_worker=None
        if error:self._manual_result={};self._set_manual("error","",MANUAL_CHECK_ERROR_MESSAGE);return
        result_host=_safe_private_host(result.get("host",""))
        if not requested or result_host!=requested:self._manual_result={};self._set_manual("error","","Результат перевірки не відповідає поточній адресі");return
        if not result.get("camera"):self._manual_result={};self._set_manual("error","","На цій адресі не знайдено доступної камери");return
        self._manual_result=result;self._remember_host(result_host,result.get("openipc",False))
        if result.get("openipc") and result.get("identityVerified"):
            identity=normalize_openipc_identity(result.get("identity",{}),result.get("evidence",[]));self._manual_result["identity"]=identity;self._set_manual("verified","OpenIPC підтверджено")
        elif result.get("authRequired"):self._set_manual("auth-required","Камера доступна. Для підтвердження OpenIPC потрібен логін.")
        else:self._set_manual("candidate","Камера доступна, але OpenIPC не підтверджено.")
    @Slot(str,str,str,str,result=str)
    def authenticateAndAdd(self,host,name,username,password):
        address=_safe_private_host(host)
        if not address:self._set_manual("error","","Некоректна адреса камери");return ""
        result=fingerprint(address,threading.Event(),str(username or "").strip(),str(password or ""))
        if not result.get("openipc") or not result.get("identityVerified"):
            self._set_manual("error","","Невірний логін/пароль або OpenIPC не підтверджено");return ""
        self._manual_result=result
        for index,item in enumerate(self._discovered):
            if item.get("host")==address:self._discovered[index]=result;break
        else:self._discovered.append(result)
        self.discoveryChanged.emit();did=self.addDiscovered(address,name,True)
        if did:self._set_manual("added","Камеру додано")
        else:self._set_manual("error","","Не вдалося додати підтверджену камеру")
        return did
    @Slot(str,str,bool,result=str)
    def addDiscovered(self,host,name,verified):
        address=_safe_private_host(host)
        if not address:self._set_manual("error","","Некоректна адреса камери");return ""
        candidate=next((x for x in self._discovered if _safe_private_host(x.get("host",""))==address),None)
        if not candidate and _safe_private_host(self._manual_result.get("host",""))==address:candidate=self._manual_result
        identity=normalize_openipc_identity(candidate.get("identity",{}),candidate.get("evidence",[])) if candidate else normalize_openipc_identity()
        if not candidate or not candidate.get("openipc") or not candidate.get("identityVerified") or not identity.get("verified"):
            self._set_manual("error","","OpenIPC identity недостатньо підтверджена для додавання");return ""
        self._remember_host(address,True);existing=next((x for x in self._items if _safe_private_host(x.get("host",""))==address),None)
        if existing:self._manual_result=candidate;self._set_manual("added","Камера вже додана");return existing["id"]
        did=self.addDevice(name or "OpenIPC "+address,"OpenIPC",address,80,"Network","")
        if not did:self._set_manual("error","","Не вдалося зберегти камеру");return ""
        self._save_identity(did,identity)
        for stream in candidate.get("streams",[]):self.addStream(did,stream.get("name","Відео"),stream.get("name","main"),int(stream.get("port",554)),stream.get("path","/"),stream.get("protocol","rtsp"))
        self._load();self.changed.emit();self._manual_result=candidate;self._set_manual("added","Камеру додано");return did
    @Slot(str,str,str,int,str,result=bool)
    def updateDevice(self,did,name,host,port,notes):
        name=name.strip();host=host.strip();from devices import valid_host
        if not name or not valid_host(host):return False
        try:
            with self._connect() as db:db.execute("UPDATE devices SET name=?,host=?,port=?,notes=? WHERE id=?",(name,host,max(1,min(int(port),65535)),notes.strip(),did))
        except Exception:return False
        self._remember_host(host,False);self._load();self.changed.emit();return True
