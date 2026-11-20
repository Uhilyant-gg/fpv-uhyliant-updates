import concurrent.futures
import ipaddress
import json
import os
import re
import socket
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
DB = DATA / "devices.json"
SERVICES = ("_http._tcp.local.", "_rtsp._tcp.local.", "_ssh._tcp.local.")
WS_DISCOVERY = ("239.255.255.250", 3702)
MAX_WORKERS = 32
HOST_LABEL_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")


def normalize_host(host):
    host = host.strip().rstrip(".")
    if not host or len(host) > 253 or "://" in host or any(char.isspace() for char in host):
        raise ValueError("Вкажіть коректний IPv4/IPv6 або hostname без протоколу та шляху")
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        pass
    if not all(HOST_LABEL_RE.fullmatch(label) for label in host.split(".")):
        raise ValueError("Некоректний IP/hostname пристрою")
    return host.lower()


def normalize_port(port):
    try:
        value = int(port)
    except (TypeError, ValueError) as error:
        raise ValueError("Порт має бути числом від 1 до 65535") from error
    if not 1 <= value <= 65535:
        raise ValueError("Порт має бути від 1 до 65535")
    return value


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
    if cancel.is_set():
        return host, False, []
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return host, False, []
    evidence = []
    verified = False
    try:
        request = urllib.request.Request(f"<scrubbed-url-domain>", headers={"Accept": "application/json", "User-Agent": "FPV-Uhyliant"})
        with urllib.request.urlopen(request, timeout=0.45) as response:
            data = json.loads(response.read(524288).decode("utf-8"))
        if isinstance(data, dict) and data and any(key in data for key in ("video0", "video1", "system", "fpv", "isp", "rtsp")):
            verified = True
            evidence.append("Majestic /api/v1/config.json")
    except (urllib.error.URLError, TimeoutError, socket.timeout, UnicodeError, json.JSONDecodeError, OSError):
        pass
    if cancel.is_set():
        return host, verified, evidence
    try:
        request = urllib.request.Request(f"<scrubbed-url-domain>", headers={"User-Agent": "FPV-Uhyliant"})
        with urllib.request.urlopen(request, timeout=0.35) as response:
            body = response.read(65536).decode("utf-8", "ignore").lower()
        if "openipc" in body or "majestic" in body:
            verified = True
            evidence.append("OpenIPC/Majestic WebUI :85")
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
        pass
    return host, verified, evidence


def onvif(found, cancel, bind_ip, network):
    for probe_type in ("dn:NetworkVideoTransmitter", ""):
        if cancel.is_set(): return
        message_id = str(uuid.uuid4())
        types = f"<d:Types>{probe_type}</d:Types>" if probe_type else ""
        payload = ('<?xml version="1.0"?>' '<e:Envelope xmlns:e="http://<scrubbed-url-domain>/2003/05/soap-envelope" ' 'xmlns:w="http://<scrubbed-url-domain>/ws/2004/08/addressing" ' 'xmlns:d="http://<scrubbed-url-domain>/ws/2005/04/discovery" ' 'xmlns:dn="http://<scrubbed-url-domain>/ver10/network/wsdl">' "<e:Header><w:MessageID>uuid:" + message_id + "</w:MessageID>" "<w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>" "<w:Action>http://<scrubbed-url-domain>/ws/2005/04/discovery/Probe</w:Action>" "</e:Header><e:Body><d:Probe>" + types + "</d:Probe></e:Body></e:Envelope>").encode("utf-8")
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
                text = data.decode("utf-8", "ignore"); hint = "openipc" in text.lower()
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
                        properties = {key.decode(errors="ignore").lower(): value.decode(errors="ignore") for key, value in info.properties.items()}; server = (info.server or "").rstrip("."); vendor = properties.get("vendor", "").strip().lower(); verified = vendor == "openipc"; hint = "openipc" in name.lower() or "openipc" in server.lower(); evidence = "mDNS vendor=OpenIPC" if verified else ("mDNS OpenIPC name hint" if hint else "mDNS")
                        for host in info.parsed_addresses():
                            try:
                                if ipaddress.ip_address(host) not in interface_network: continue
                            except ValueError: continue
                            merge(found, host, server or name.split(".")[0], service_type, verified, evidence)
                        worker.live.emit(list(found.values())); worker.emit_progress("mDNS", found=len(found))
                    except (OSError, UnicodeError, ValueError): pass
                def update_service(self, zeroconf, service_type, name): self.add_service(zeroconf, service_type, name)
                def remove_service(self, zeroconf, service_type, name): pass
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
                scan_network = ipaddress.ip_network(bind_ip + "/24", strict=False); hosts = [str(host) for host in scan_network.hosts() if str(host) != bind_ip]; total = len(hosts); completed = 0; self.emit_progress("/24", 0, total, len(found)); executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS); pending = {executor.submit(probe, host, self.cancel) for host in hosts}
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
        super().__init__(); DATA.mkdir(parents=True, exist_ok=True); self._items=[]; self._active_id=""; self._discovered=[]; self._scanning=False; self._worker=None; self._stage="Готово"; self._pd=0; self._pt=0; self._found=0; self._status="Готово"; self._interfaces=[]; self._selected_interface=""; self._load(); self.refreshInterfaces()
    def _load(self):
        try:
            raw=json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {}; devices=raw.get("devices", []); self._items=devices if isinstance(devices,list) else []; self._active_id=raw.get("activeDeviceId", "")
            if not any(item.get("id")==self._active_id for item in self._items): self._active_id=self._items[0].get("id","") if self._items else ""
        except (OSError,UnicodeError,json.JSONDecodeError,AttributeError): self._items=[]; self._active_id=""
    def _save(self):
        temporary=DB.with_suffix(".tmp"); temporary.write_text(json.dumps({"schema":1,"activeDeviceId":self._active_id,"devices":self._items},ensure_ascii=False,indent=2),encoding="utf-8"); os.replace(temporary,DB)
    def _public_item(self,item): return {**item,"active":item.get("id")==self._active_id}
    @Property("QVariantList",notify=changed)
    def items(self): return [self._public_item(item) for item in self._items]
    @Property(int,notify=changed)
    def count(self): return len(self._items)
    @Property(str,notify=changed)
    def activeName(self): return next((item.get("name","") for item in self._items if item.get("id")==self._active_id),"")
    @Property(str,notify=changed)
    def activeSummary(self): return next((f"{item.get('type','')} · {item.get('host','')}" for item in self._items if item.get("id")==self._active_id),"")
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
        self._interfaces=interfaces(); ids=[item["id"] for item in self._interfaces]
        if self._selected_interface not in ids: self._selected_interface=ids[0] if ids else ""
        self.discoveryChanged.emit()
    @Slot(str)
    def setSelectedInterface(self,interface_id):
        if not self._scanning and any(item["id"]==interface_id for item in self._interfaces): self._selected_interface=interface_id; self.discoveryChanged.emit()
    @Slot()
    def discoverOpenIPC(self):
        if self._scanning: return
        iface=next((item for item in self._interfaces if item["id"]==self._selected_interface),None)
        if not iface: self._status="Помилка"; self.notice.emit("Немає вибраного IPv4 мережевого інтерфейсу"); self.discoveryChanged.emit(); return
        self._scanning=True; self._discovered=[]; self._stage="mDNS"; self._pd=self._pt=self._found=0; self._status="Сканування"; self.discoveryChanged.emit(); self._worker=Worker(iface); self._worker.progress.connect(self._progress); self._worker.live.connect(self._live); self._worker.done.connect(self._done); self._worker.finished.connect(self._worker_finished); self._worker.start()
    @Slot()
    def cancelDiscovery(self):
        if self._scanning and self._worker: self._status="Скасування"; self.discoveryChanged.emit(); self._worker.stop()
    @Slot(str,int,int,int)
    def _progress(self,stage,done,total,found): self._stage,self._pd,self._pt,self._found=stage,done,total,found; self.discoveryChanged.emit()
    @Slot(object)
    def _live(self,result): self._discovered=list(result); self._found=len(result); self.discoveryChanged.emit()
    @Slot(object,bool,str)
    def _done(self,result,cancelled,error): self._discovered=list(result); self._found=len(result); self._scanning=False; self._status="Помилка" if error else ("Скасовано" if cancelled else "Завершено"); self.discoveryChanged.emit(); self.notice.emit((error or self._status)+f": {len(result)} знайдено")
    @Slot()
    def _worker_finished(self):
        worker=self.sender()
        if worker is self._worker: self._worker=None
        if worker: worker.deleteLater()
    @Slot(str,str,bool,result=str)
    def addDiscovered(self,host,name,confirmed):
        if not confirmed: return ""
        try: host=normalize_host(host)
        except ValueError as error: self.notice.emit(str(error)); return ""
        for item in self._items:
            if item.get("host")==host: self._active_id=item["id"]; self._save(); self.changed.emit(); return item["id"]
        return self.addDevice(name or "OpenIPC "+host,"Камера OpenIPC",host,80,"Мережа","OpenIPC verified")
    @Slot(str,str,str,int,str,str,result=str)
    def addDevice(self,name,device_type,host,port,connection,note):
        name=name.strip()
        if not name: self.notice.emit("Назва пристрою обов'язкова"); return ""
        try: host=normalize_host(host); port=normalize_port(port)
        except ValueError as error: self.notice.emit(str(error)); return ""
        device_id=uuid.uuid4().hex; self._items.append({"id":device_id,"name":name,"type":device_type,"host":host,"port":port,"connection":connection,"notes":note.strip()}); self._active_id=self._active_id or device_id; self._save(); self.changed.emit(); return device_id
    @Slot(str,str,str,int,str,result=bool)
    def updateDevice(self,device_id,name,host,port,note):
        try: host=normalize_host(host); port=normalize_port(port)
        except ValueError as error: self.notice.emit(str(error)); return False
        for item in self._items:
            if item.get("id")==device_id:
                item["name"]=name.strip() or item["name"]; item["host"]=host; item["port"]=port; item["notes"]=note.strip(); self._save(); self.changed.emit(); return True
        return False
    @Slot(str)
    def setActive(self,device_id):
        if any(item.get("id")==device_id for item in self._items): self._active_id=device_id; self._save(); self.changed.emit()
    @Slot(str)
    def removeDevice(self,device_id):
        self._items=[item for item in self._items if item.get("id")!=device_id]
        if self._active_id==device_id: self._active_id=self._items[0]["id"] if self._items else ""
        self._save(); self.changed.emit()
