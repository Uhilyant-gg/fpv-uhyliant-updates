"""Strict validation for portable station snapshots before transactional restore."""
import ipaddress,re
HOST_RE=re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*\.?$")
def valid_host(host):
 host=str(host).strip()
 if not host or '://' in host or '/' in host or '\\' in host or any(c.isspace() for c in host):return False
 try:ip=ipaddress.ip_address(host);return ip.version==4 and not(ip.is_unspecified or ip.is_multicast)
 except ValueError:return bool(HOST_RE.fullmatch(host))
def _int(value,low,high,nullable=False):
 if nullable and value is None:return True
 return isinstance(value,int) and not isinstance(value,bool) and low<=value<=high
def validate_snapshot(value):
 if not isinstance(value,dict) or set(value)!={'devices','streams','videoProfiles','openipcIdentities','activeDeviceId'}:return False
 if not all(isinstance(value[k],list) for k in ('devices','streams','videoProfiles','openipcIdentities')) or not isinstance(value['activeDeviceId'],str):return False
 devices=value['devices'];ids=set();hostports=set()
 for d in devices:
  if not isinstance(d,dict) or set(d)!={'id','name','type','host','port','connection','notes'} or not all(isinstance(d.get(k),str) for k in ('id','name','type','host','connection','notes')):return False
  if not d['id'] or not d['name'] or not valid_host(d['host']) or not _int(d['port'],1,65535) or d['id'] in ids or (d['host'],d['port']) in hostports:return False
  ids.add(d['id']);hostports.add((d['host'],d['port']))
 if value['activeDeviceId'] and value['activeDeviceId'] not in ids:return False
 profiles=set();names=set()
 for p in value['videoProfiles']:
  required={'id','name','codec','width','height','fps','bitrate_kbps','latency_mode','notes'}
  if not isinstance(p,dict) or set(p)!=required or not all(isinstance(p.get(k),str) for k in ('id','name','codec','latency_mode','notes')):return False
  if not p['id'] or not p['name'] or p['codec'] not in ('h264','h265') or p['id'] in profiles or p['name'] in names:return False
  if not all(_int(p[k],1,1000000,True) for k in ('width','height','fps','bitrate_kbps')):return False
  profiles.add(p['id']);names.add(p['name'])
 stream_ids=set();device_kinds=set()
 for s in value['streams']:
  required={'id','device_id','name','kind','protocol','port','path','video_profile_id','enabled'}
  if not isinstance(s,dict) or set(s)!=required or not all(isinstance(s.get(k),str) for k in ('id','device_id','name','kind','protocol','path')):return False
  if not s['id'] or s['device_id'] not in ids or not s['name'] or s['protocol'] not in ('rtsp','udp','tcp') or not s['path'].startswith('/') or not _int(s['port'],1,65535) or not isinstance(s['enabled'],bool):return False
  if s['video_profile_id'] is not None and (not isinstance(s['video_profile_id'],str) or s['video_profile_id'] not in profiles):return False
  if s['id'] in stream_ids or (s['device_id'],s['kind']) in device_kinds:return False
  stream_ids.add(s['id']);device_kinds.add((s['device_id'],s['kind']))
 identity_devices=set()
 for i in value['openipcIdentities']:
  required={'device_id','verified','platform','soc','sensor','firmware','majestic','evidence'}
  if not isinstance(i,dict) or set(i)!=required or i.get('device_id') not in ids or i.get('verified') is not True or i['device_id'] in identity_devices:return False
  if not all(isinstance(i.get(k),str) for k in ('platform','soc','sensor','firmware','majestic')) or not isinstance(i.get('evidence'),list) or not all(isinstance(e,str) for e in i['evidence']):return False
  identity_devices.add(i['device_id'])
 return True
