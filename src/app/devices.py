import concurrent.futures
import ipaddress
import json
import os
import re
import socket
import sqlite3
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import psutil
from PySide6.QtCore import QObject, Property, QThread, Signal, Slot
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FPV-Uhyliant"
LEGACY_DB = DATA / "devices.json"
DB = DATA / "devices.sqlite3"
SERVICES = ("_http._tcp.local.", "_rtsp._tcp.local.", "_ssh._tcp.local.")
WS_DISCOVERY = ("239.255.255.250", 3702)
MAX_WORKERS = 32
HOST_RE = re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*\.?$")


def valid_host(host):
    host = host.strip()
    if not host or "://" in host or "/" in host or "\\" in host or any(ch.isspace() for ch in host):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return ip.version == 4 and not (ip.is_unspecified or ip.is_multicast)
    except ValueError:
        return bool(HOST_RE.fullmatch(host))


def merge(found, host, name="", service="", verified=False, evidence=""):
    if not host:
        return
    item = found.setdefault(host, {"name": name or host, "host": host, "hostname": name or host, "services": [], "openipc": False, "evidence": []})
    if name and item["name"] == host:
        item["name"] = name
        item["hostname"] = name
    if service and service not in item["services"]:
        item["services"].append(service)
    if verified:
        item["openipc"] = True
    if evidence and evidence not in item["evidence"]:
        item["evidence"].append(evidence)


def interfaces():
    result = []
    stats = psutil.net_if_stats()
    for name, addresses in psutil.net_if_addrs().items():
        if name in stats and not stats[name].isup:
            continue
        for address in addresses:
            if address.family != socket.AF_INET or not address.address or address.address.startswith("127."):
                continue
            mask = address.netmask or "255.255.255.0"
            try:
                network = str(ipaddress.ip_network(f"{address.address}/{mask}", strict=False))
            except ValueError:
                network = str(ipaddress.ip_network(f"{address.address}/24", strict=False))
            result.append({"id": f"{name}|{address.address}", "name": name, "address": address.address, "netmask": mask, "network": network, "label": f"{name} — {address.address} — {network}"})
    return result


def probe(host, cancel):
    if cancel.is_set(): return host, False, []
    try: ipaddress.ip_address(host)
    except ValueError: return host, False, []
    evidence, verified = [], False
    for url, label, json_mode in ((f"<scrubbed-url-domain>", "Majestic /api/v1/config.json", True), (f"<scrubbed-url-domain>", "OpenIPC/Majestic WebUI :85", False)):
        if cancel.is_set(): break
        try:
            request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "FPV-Uhyliant"})
            with urllib.request.urlopen(request, timeout=0.45) as response: raw = response.read(524288 if json_mode else 65536)
            if json_mode:
                data = json.loads(raw.decode("utf-8"))
                matched = isinstance(data, dict) and data and any(k in data for k in ("video0", "video1", "system", "fpv", "isp", "rtsp"))
            else:
                body = raw.decode("utf-8", "ignore").lower(); matched = "openipc" in body or "majestic" in body
            if matched: verified = True; evidence.append(label)
        except (urllib.error.URLError, TimeoutError, socket.timeout, UnicodeError, json.JSONDecodeError, OSError): pass
    return host, verified, evidence


def onvif(found, cancel, bind_ip, network):
    for probe_type in ("dn:NetworkVideoTransmitter", ""):
        if cancel.is_set(): return
        message_id = str(uuid.uuid4()); types = f"<d:Types>{probe_type}</d:Types>" if probe_type else ""
        payload = ('<?xml version="1.0"?><e:Envelope xmlns:e="http://<scrubbed-url-domain>/2003/05/soap-envelope" xmlns:w="http://<scrubbed-url-domain>/ws/2004/08/addressing" xmlns:d="http://<scrubbed-url-domain>/ws/2005/04/discovery" xmlns:dn="http://<scrubbed-url-domain>/ver10/network/wsdl"><e:Header><w:MessageID>uuid:' + message_id + '</w:MessageID><w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To><w:Action>http://<scrubbed-url-domain>/ws/2005/04/discovery/Probe</w:Action></e:Header><e:Body><d:Probe>' + types + '</d:Probe></e:Body></e:Envelope>').encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            sock.bind((bind_ip, 0)); sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(bind_ip)); sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2); sock.settimeout(0.2)
            for _ in range(2): sock.sendto(payload, WS_DISCOVERY)
            deadline = time.monotonic() + 2.5
            while time.monotonic() < deadline and not cancel.is_set():
                try: data, source = sock.recvfrom(65535)
                except socket.timeout: continue
                host = source[0]
                try:
                    if ipaddress.ip_address(host) not in network: continue
                except ValueError: continue
                hint = "openipc" in data.decode("utf-8", "ignore").lower()
                merge(found, host, "ONVIF " + host, "ONVIF", False, "ONVIF OpenIPC hint" if hint else "ONVIF WS-Discovery")
        finally: sock.close()


def host_sort_key(item):
    try: host = (0, int(ipaddress.ip_address(item["host"])))
    except ValueError: host = (1, item["host"].lower())
    return not item["openipc"], host


class Worker(QThread):
    done = Signal(object, bool, str); progress = Signal(str, int, int, int); live = Signal(object)
    def __init__(self, iface): super().__init__(); self.cancel = threading.Event(); self.iface = iface
    def stop(self): self.cancel.set(); self.requestInterruption()
    def emit_progress(self, stage, done=0, total=0, found=0): self.progress.emit(stage, done, total, found)
    def run(self):
        found = {}; worker = self; bind_ip = self.iface["address"]; interface_network = ipaddress.ip_network(self.iface["network"], strict=False)
        try:
            self.emit_progress("mDNS")
            class Listener(ServiceListener):
                def add_service(self, zeroconf, service_type, name):
                    if worker.cancel.is_set(): return
                    try:
                        info = zeroconf.get_service_info(service_type, name, timeout=800)
                        if not info: return
                        properties = {k.decode(errors="ignore").lower(): v.decode(errors="ignore") for k, v in info.properties.items()}; server = (info.server or "").rstrip("."); vendor = properties.get("vendor", "").strip().lower(); verified = vendor == "openipc"; hint = "openipc" in name.lower() or "openipc" in server.lower(); evidence = "mDNS vendor=OpenIPC" if verified else ("mDNS OpenIPC name hint" if hint else "mDNS")
                        for host in info.parsed_addresses():
                            try:
                                if ipaddress.ip_address(host) not in interface_network: continue
                            except ValueError: continue
                            merge(found, host, server or name.split(".")[0], service_type, verified, evidence)
                        worker.live.emit(list(found.values())); worker.emit_progress("mDNS", found=len(found))
                    except (OSError, UnicodeError, ValueError): pass
                def update_service(self, z, t, n): self.add_service(z, t, n)
                def remove_service(self, z, t, n): pass
            zeroconf = Zeroconf(interfaces=[bind_ip]); listener = Listener(); browsers = [ServiceBrowser(zeroconf, service, listener) for service in SERVICES]; deadline = time.monotonic() + 3.5
            while time.monotonic() < deadline and not self.cancel.is_set(): self.msleep(100)
            for browser in browsers: browser.cancel()
            zeroconf.close()
            if not self.cancel.is_set(): self.emit_progress("ONVIF", found=len(found)); onvif(found, self.cancel, bind_ip, interface_network); self.live.emit(list(found.values()))
            if not self.cancel.is_set():
                targets = list(found); self.emit_progress("fingerprint", 0, len(targets), len(found))
                for index, host in enumerate(targets, 1):
                    if self.cancel.is_set(): break
                    _, verified, evidence = probe(host, self.cancel)
                    if verified:
                        merge(found, host, service="Majestic/OpenIPC fingerprint", verified=True)
                        for reason in evidence: merge(found, host, evidence=reason)
                    self.emit_progress("fingerprint", index, len(targets), len(found)); self.live.emit(list(found.values()))
            if not self.cancel.is_set():
                scan_network = ipaddress.ip_network(bind_ip + "/24", strict=False); hosts = [str(h) for h in scan_network.hosts() if str(h) != bind_ip]; total = len(hosts); completed = 0; self.emit_progress("/24", 0, total, len(found)); executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS); pending = {executor.submit(probe, host, self.cancel) for host in hosts}
                try:
                    while pending and not self.cancel.is_set():
                        finished, pending = concurrent.futures.wait(pending, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                        for future in finished:
                            completed += 1
                            try: host, verified, evidence = future.result()
                            except Exception: continue
                            if verified:
                                merge(found, host, "OpenIPC " + host, "/24 fingerprint", True)
                                for reason in evidence: merge(found, host, evidence=reason)
                            self.emit_progress("/24", completed, total, len(found))
                        if finished: self.live.emit(list(found.values()))
                finally:
                    if self.cancel.is_set():
                        for future in pending: future.cancel()
                    executor.shutdown(wait=not self.cancel.is_set(), cancel_futures=True)
            result = list(found.values())
            for item in result: item["confidence"] = "OpenIPC підтверджено" if item["openipc"] else "Кандидат, не підтверджено"
            result.sort(key=host_sort_key); self.done.emit(result, self.cancel.is_set(), "")
        except Exception as error: self.done.emit(list(found.values()), self.cancel.is_set(), str(error))


class Devices(QObject):
    changed = Signal(); notice = Signal(str); discoveryChanged = Signal()
    def __init__(self):
        super().__init__(); DATA.mkdir(parents=True, exist_ok=True); self._items=[]; self._active_id=""; self._discovered=[]; self._scanning=False; self._worker=None; self._stage="Готово"; self._pd=0; self._pt=0; self._found=0; self._status="Готово"; self._interfaces=[]; self._selected_interface=""; self._init_db(); self._load(); self.refreshInterfaces()
    def _connect(self): return sqlite3.connect(DB, timeout=5)
    def _init_db(self):
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL"); db.execute("CREATE TABLE IF NOT EXISTS devices (id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, host TEXT NOT NULL, port INTEGER NOT NULL, connection TEXT NOT NULL, notes TEXT NOT NULL)"); db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_host_port ON devices(host, port)"); db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            count = db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
            if count == 0 and LEGACY_DB.exists():
                try:
                    raw=json.loads(LEGACY_DB.read_text(encoding="utf-8")); items=raw.get("devices", []) if isinstance(raw, dict) else []
                    for item in items:
                        host=str(item.get("host", "")).strip()
                        if item.get("id") and item.get("name") and valid_host(host): db.execute("INSERT OR IGNORE INTO devices VALUES (?,?,?,?,?,?,?)", (item["id"], item["name"], item.get("type", "Пристрій"), host, max(1,min(int(item.get("port",80)),65535)), item.get("connection","Мережа"), item.get("notes","")))
                    active=raw.get("activeDeviceId", ""); db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('activeDeviceId',?)", (active,))
                    LEGACY_DB.rename(LEGACY_DB.with_suffix(".json.migrated"))
                except (OSError, ValueError, TypeError, json.JSONDecodeError): pass
    def _load(self):
        try:
            with self._connect() as db:
                cols="id,name,type,host,port,connection,notes"; self._items=[dict(zip(cols.split(','), row)) for row in db.execute("SELECT "+cols+" FROM devices ORDER BY name COLLATE NOCASE")]; row=db.execute("SELECT value FROM settings WHERE key='activeDeviceId'").fetchone(); self._active_id=row[0] if row else ""
            if not any(i["id"]==self._active_id for i in self._items): self._active_id=self._items[0]["id"] if self._items else ""; self._save_active()
        except sqlite3.Error as e: self._items=[]; self._active_id=""; self.notice.emit("Помилка бази пристроїв: "+str(e))
    def _save_active(self):
        with self._connect() as db: db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('activeDeviceId',?)", (self._active_id,))
    def _public_item(self,item): return {**item,"active":item.get("id")==self._active_id}
    @Property("QVariantList",notify=changed)
    def items(self): return [self._public_item(i) for i in self._items]
    @Property(int,notify=changed)
    def count(self): return len(self._items)
    @Property(str,notify=changed)
    def activeName(self): return next((i["name"] for i in self._items if i["id"]==self._active_id),"")
    @Property(str,notify=changed)
    def activeSummary(self): return next((f"{i['type']} · {i['host']}" for i in self._items if i["id"]==self._active_id),"")
    @Property("QVariantList",notify=discoveryChanged)
    def discovered(self): return self._discovered
    @Property("QVariantList",notify=discoveryChanged)
    def networkInterfaces(self): return self._interfaces
    @Property(str,notify=discoveryChanged)
    def selectedInterfaceId(self): return self._selected_interface
    @Property(bool,notify=discoveryChanged)
    def scanning(self): return self._scanning
    @Property(str,notify=discoveryChanged)
    def scanStage(self): return self._stage
    @Property(int,notify=discoveryChanged)
    def scanDone(self): return self._pd
    @Property(int,notify=discoveryChanged)
    def scanTotal(self): return self._pt
    @Property(int,notify=discoveryChanged)
    def foundCount(self): return self._found
    @Property(str,notify=discoveryChanged)
    def scanStatus(self): return self._status
    @Slot()
    def refreshInterfaces(self):
        self._interfaces=interfaces(); ids=[i["id"] for i in self._interfaces]; self._selected_interface=self._selected_interface if self._selected_interface in ids else (ids[0] if ids else ""); self.discoveryChanged.emit()
    @Slot(str)
    def setSelectedInterface(self,interface_id):
        if not self._scanning and any(i["id"]==interface_id for i in self._interfaces): self._selected_interface=interface_id; self.discoveryChanged.emit()
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
    def _progress(self,stage,done,total,found):self._stage,self._pd,self._pt,self._found=stage,done,total,found;self.discoveryChanged.emit()
    @Slot(object)
    def _live(self,result):self._discovered=list(result);self._found=len(result);self.discoveryChanged.emit()
    @Slot(object,bool,str)
    def _done(self,result,cancelled,error):self._discovered=list(result);self._found=len(result);self._scanning=False;self._status="Помилка" if error else ("Скасовано" if cancelled else "Завершено");self.discoveryChanged.emit();self.notice.emit((error or self._status)+f": {len(result)} знайдено")
    @Slot()
    def _worker_finished(self):
        worker=self.sender(); self._worker=None if worker is self._worker else self._worker
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
        port=max(1,min(int(port),65535)); device_id=uuid.uuid4().hex
        try:
            with self._connect() as db: db.execute("INSERT INTO devices VALUES (?,?,?,?,?,?,?)",(device_id,name,device_type,host,port,connection,note.strip()))
        except sqlite3.IntegrityError:self.notice.emit("Пристрій з таким host і портом уже існує");return ""
        self._active_id=self._active_id or device_id;self._save_active();self._load();self.changed.emit();return device_id
    @Slot(str,str,str,int,str,result=bool)
    def updateDevice(self,device_id,name,host,port,note):
        name,host=name.strip(),host.strip()
        if not name or not valid_host(host):self.notice.emit("Вкажіть коректні назву та IPv4/hostname без схеми URL або шляху");return False
        port=max(1,min(int(port),65535))
        try:
            with self._connect() as db: cur=db.execute("UPDATE devices SET name=?,host=?,port=?,notes=? WHERE id=?",(name,host,port,note.strip(),device_id))
        except sqlite3.IntegrityError:self.notice.emit("Пристрій з таким host і портом уже існує");return False
        if not cur.rowcount:return False
        self._load();self.changed.emit();return True
    @Slot(str)
    def setActive(self,device_id):
        if any(i["id"]==device_id for i in self._items):self._active_id=device_id;self._save_active();self.changed.emit()
    @Slot(str)
    def removeDevice(self,device_id):
        with self._connect() as db: db.execute("DELETE FROM devices WHERE id=?",(device_id,))
        if self._active_id==device_id:self._active_id=""
        self._load();self.changed.emit()
