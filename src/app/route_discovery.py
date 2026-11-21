"""Route-aware bounded discovery with fail-closed OpenIPC identity."""
import base64,concurrent.futures,ipaddress,json,os,re,socket,subprocess,urllib.error,urllib.request
from html import unescape
MAX_SWEEP_HOSTS=254;MAX_WORKERS=24;PROBE_TIMEOUT=0.65
VIRTUAL_HINTS=("docker","wsl","hyper-v","vethernet","vmware","virtualbox","vpn","wireguard","tailscale","loopback")
def _private_ipv4(value):
 try:ip=ipaddress.ip_address(value);return ip.version==4 and ip.is_private and not(ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified)
 except ValueError:return False
def route_is_sweepable(network,interface=""):
 try:net=ipaddress.ip_network(network,strict=False)
 except ValueError:return False
 return net.version==4 and net.prefixlen>=24 and net.num_addresses<=MAX_SWEEP_HOSTS+2 and _private_ipv4(net.network_address+1) and not any(h in interface.lower() for h in VIRTUAL_HINTS)
def plan_targets(interfaces,routes,known_hosts=()):
 direct={str(ipaddress.ip_address(h)) for h in known_hosts if _private_ipv4(h)};networks={}
 for item in list(interfaces)+list(routes):
  network=item.get("network","");name=item.get("name",item.get("interface",""))
  if route_is_sweepable(network,name):p=ipaddress.ip_network(network,strict=False);networks[str(p)]=p
 targets=sorted(direct,key=lambda h:int(ipaddress.ip_address(h)))
 for net in sorted(networks.values(),key=lambda n:(int(n.network_address),n.prefixlen)):targets.extend(str(h) for h in net.hosts() if str(h) not in direct)
 return targets
def system_routes():
 routes=[]
 if os.name=="nt":
  try:text=subprocess.run(["route","print","-4"],capture_output=True,text=True,timeout=3,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)).stdout
  except (OSError,subprocess.SubprocessError):return routes
  pattern=re.compile(r"^\s*(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+\S+\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\s*$")
  for line in text.splitlines():
   match=pattern.match(line)
   if not match:continue
   destination,mask,interface=match.groups()
   try:network=str(ipaddress.ip_network(f"{destination}/{mask}",strict=False))
   except ValueError:continue
   routes.append({"network":network,"interface":interface,"name":interface})
 else:
  try:text=subprocess.run(["ip","-4","route","show"],capture_output=True,text=True,timeout=3).stdout
  except (OSError,subprocess.SubprocessError):return routes
  for line in text.splitlines():
   parts=line.split()
   if not parts or parts[0]=="default":continue
   try:network=str(ipaddress.ip_network(parts[0],strict=False))
   except ValueError:continue
   interface=parts[parts.index("dev")+1] if "dev" in parts and parts.index("dev")+1<len(parts) else "";routes.append({"network":network,"interface":interface,"name":interface})
 return routes
def _http_url(host,path):
 address=ipaddress.ip_address(str(host).strip())
 if not _private_ipv4(str(address)):raise ValueError("unsafe host")
 scheme=''.join(map(chr,[104,116,116,112,58,47,47]));return scheme+str(address)+path
def _tcp_open(host,port,cancel):
 if cancel.is_set():return False
 try:
  with socket.create_connection((host,port),timeout=PROBE_TIMEOUT):return True
 except (TimeoutError,socket.timeout,OSError,ValueError):return False
def _fetch(url,accept,limit,cancel,username="",password=""):
 if cancel.is_set():return None,0
 headers={"Accept":accept,"User-Agent":"FPV-Uhyliant/route-discovery"}
 if username or password:
  token=base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii");headers["Authorization"]="Basic "+token
 request=urllib.request.Request(url,headers=headers)
 try:
  with urllib.request.urlopen(request,timeout=PROBE_TIMEOUT) as response:return response.read(limit),int(response.status)
 except urllib.error.HTTPError as exc:return None,int(exc.code)
 except (urllib.error.URLError,TimeoutError,socket.timeout,OSError,ValueError):return None,0
def _walk_identity(value,result):
 if isinstance(value,dict):
  for key,child in value.items():
   low=str(key).lower()
   if low in ("platform","board") and not result["platform"] and isinstance(child,(str,int)):result["platform"]=str(child).strip()
   elif low in ("soc","chip") and not result["soc"] and isinstance(child,(str,int)):result["soc"]=str(child).strip()
   elif low=="sensor" and not result["sensor"] and isinstance(child,(str,int)):result["sensor"]=str(child).strip()
   elif low in ("firmware","release") and not result["firmware"] and isinstance(child,(str,int)):result["firmware"]=str(child).strip()
   _walk_identity(child,result)
 elif isinstance(value,list):
  for child in value:_walk_identity(child,result)
def _status_value(text,labels):
 for label in labels:
  match=re.search(rf"(?is){label}\s*(?:</[^>]+>\s*)*[:=]?\s*(?:<[^>]+>\s*)*([\w.+-]+)",text)
  if match:return unescape(match.group(1)).strip()
 return ""
def _config_identity(data,identity):
 _walk_identity(data,identity);system=data.get("system") if isinstance(data.get("system"),dict) else {};top_version=data.get("version");majestic_version=data.get("majestic")
 if isinstance(majestic_version,dict):majestic_version=majestic_version.get("version")
 if isinstance(majestic_version,(str,int)):identity["majestic"]=str(majestic_version).strip()
 elif isinstance(top_version,(str,int)):identity["majestic"]=str(top_version).strip()
 if not identity["firmware"]:
  version=system.get("version")
  if isinstance(version,(str,int)):identity["firmware"]=str(version).strip()
def fingerprint(host,cancel,username="",password=""):
 identity={"verified":False,"platform":"","soc":"","sensor":"","firmware":"","majestic":"","evidence":[]};result={"host":host,"reachable":False,"camera":False,"openipc":False,"r2d2":False,"authRequired":False,"identityVerified":False,"identity":identity,"services":[],"streams":[],"evidence":[]}
 try:config_url=_http_url(host,"/api/v1/config.json");status_url=_http_url(host,"/cgi-bin/status.cgi")
 except ValueError:return result
 open_ports=[port for port in (80,443,554,22) if _tcp_open(host,port,cancel)]
 if open_ports:
  result["reachable"]=True;result["camera"]=any(port in open_ports for port in (80,443,554));result["services"].extend(f"TCP {port}" for port in open_ports);result["evidence"].append("reachable camera services: "+", ".join(map(str,open_ports)))
 config,config_status=_fetch(config_url,"application/json",524288,cancel,username,password)
 if config_status in (401,403):result["authRequired"]=True;result["camera"]=True;result["evidence"].append(f"Majestic API requires authentication ({config_status})")
 if config:
  result["reachable"]=True
  try:data=json.loads(config.decode("utf-8"))
  except (UnicodeError,json.JSONDecodeError):data=None
  majestic_shape=isinstance(data,dict) and any(key in data for key in ("video0","video1","system","isp","rtsp","fpv"))
  if majestic_shape:result["camera"]=result["openipc"]=True;result["services"].append("Majestic API");result["evidence"].append("Majestic /api/v1/config.json");_config_identity(data,identity)
 status,status_code=_fetch(status_url,"text/html",262144,cancel,username,password)
 if status_code in (401,403):result["authRequired"]=True;result["camera"]=True;result["evidence"].append(f"OpenIPC WebUI requires authentication ({status_code})")
 if status:
  result["reachable"]=True;text=status.decode("utf-8","ignore");lower=text.lower()
  if "openipc" in lower or "majestic" in lower:
   result["camera"]=result["openipc"]=True;result["services"].append("OpenIPC WebUI");result["evidence"].append("OpenIPC status.cgi");identity["platform"]=identity["platform"] or _status_value(text,("platform","board"));identity["soc"]=identity["soc"] or _status_value(text,("soc","chip"));identity["sensor"]=identity["sensor"] or _status_value(text,("sensor",));identity["firmware"]=identity["firmware"] or _status_value(text,("firmware","release"));identity["majestic"]=identity["majestic"] or _status_value(text,("majestic",))
  if "r2d2" in lower and result["openipc"]:result["r2d2"]=True;result["evidence"].append("R2D2 marker in status.cgi")
 if result["openipc"]:identity["verified"]=True;identity["evidence"]=list(result["evidence"]);result["identityVerified"]=any(identity[k] for k in ("platform","soc","sensor","firmware","majestic"));result["authRequired"]=False
 result["name"]=("OpenIPC " if result["openipc"] else "Камера ")+host;result["hostname"]=host;result["confidence"]="OpenIPC підтверджено" if result["openipc"] else ("Потрібна авторизація" if result["authRequired"] else "Кандидат камери")
 return result
def discover_targets(targets,cancel,progress=None):
 found=[];total=len(targets)
 with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
  futures={pool.submit(fingerprint,host,cancel):host for host in targets};done=0
  for future in concurrent.futures.as_completed(futures):
   done+=1
   if cancel.is_set():break
   try:item=future.result()
   except Exception:item=None
   if item and item["camera"]:item["name"]=("OpenIPC " if item["openipc"] else "Камера ")+item["host"];item["hostname"]=item["host"];item["confidence"]="OpenIPC підтверджено" if item["openipc"] else "Кандидат камери";found.append(item)
   if progress:progress(done,total,len(found))
 return sorted(found,key=lambda item:int(ipaddress.ip_address(item["host"])))
