import ipaddress
from copy import deepcopy
from route_discovery import route_is_sweepable

def _ipv4(value):
 try:
  ip=ipaddress.ip_address(str(value));return str(ip) if ip.version==4 else None
 except ValueError:return None

def collect_network_evidence(interfaces,routes,devices=(),discovered=()):
 evidence={'interfaces':[],'routes':[],'devices':[],'summary':{'usableInterfaces':0,'safeRoutes':0,'knownDevices':0,'verifiedOpenIPC':0}}
 seen_interfaces=set()
 for item in interfaces or ():
  if not isinstance(item,dict):continue
  address=_ipv4(item.get('address') or item.get('name'))
  if not address or address in seen_interfaces:continue
  seen_interfaces.add(address);network=str(item.get('network') or '')
  evidence['interfaces'].append({'name':str(item.get('name') or ''),'address':address,'network':network or None,'usable':bool(network and route_is_sweepable(network,str(item.get('name') or '')))})
 for item in routes or ():
  if not isinstance(item,dict):continue
  network=str(item.get('network') or '');interface=str(item.get('interface',item.get('name','')) or '')
  if not network:continue
  evidence['routes'].append({'network':network,'interface':interface or None,'safeForDiscovery':route_is_sweepable(network,interface)})
 observed={}
 for item in list(devices or ())+list(discovered or ()):
  if not isinstance(item,dict):continue
  host=_ipv4(item.get('host'))
  if not host:continue
  identity=item.get('openipcIdentity') or item.get('identity') or {};verified=bool(item.get('openipc') or identity.get('verified'))
  current=observed.setdefault(host,{'host':host,'saved':False,'discovered':False,'reachable':None,'openipcVerified':False})
  current['saved']=current['saved'] or item in (devices or ())
  current['discovered']=current['discovered'] or item in (discovered or ())
  if 'reachable' in item:current['reachable']=bool(item.get('reachable'))
  current['openipcVerified']=current['openipcVerified'] or verified
 evidence['devices']=sorted(observed.values(),key=lambda x:int(ipaddress.ip_address(x['host'])))
 evidence['summary']={'usableInterfaces':sum(1 for x in evidence['interfaces'] if x['usable']),'safeRoutes':sum(1 for x in evidence['routes'] if x['safeForDiscovery']),'knownDevices':len(evidence['devices']),'verifiedOpenIPC':sum(1 for x in evidence['devices'] if x['openipcVerified'])}
 return deepcopy(evidence)
