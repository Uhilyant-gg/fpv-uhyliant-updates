import json,os,sqlite3,uuid
from contextlib import closing,contextmanager
from pathlib import Path
from PySide6.QtCore import QObject,Property,Signal,Slot
from device_center import device_center_fields
DATA=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'FPV-Uhyliant';DB=DATA/'station.db'
def valid_host(v):
 import ipaddress
 try:a=ipaddress.ip_address(v);return not(a.is_unspecified or a.is_multicast or a.is_loopback)
 except ValueError:return False
def interfaces():
 import socket,ipaddress
 out=[]
 try:
  for _,_,_,_,sa in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):
   ip=sa[0]
   if valid_host(ip):out.append({'name':ip,'address':ip,'network':str(ipaddress.ip_network(ip+'/24',strict=False))})
 except OSError:pass
 return out
class Devices(QObject):
 changed=Signal();streamsChanged=Signal();discoveryChanged=Signal();deviceAdded=Signal();deviceUpdated=Signal();deviceRemoved=Signal();deviceListRestored=Signal()
 def __init__(self):
  super().__init__();DATA.mkdir(parents=True,exist_ok=True);self._items=[];self._streams=[];self._active='';self._discovered=[];self._scanning=False;self._stage='';self._status='';self._pd=0;self._pt=0;self._found=0;self._worker=None;self._init();self._load()
 @contextmanager
 def _connect(self):
  with closing(sqlite3.connect(DB)) as connection:
   with connection:yield connection
 def _init(self):
  with self._connect() as d:
   d.execute('CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY,name TEXT NOT NULL,type TEXT NOT NULL,host TEXT NOT NULL,port INTEGER NOT NULL,connection TEXT NOT NULL,notes TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 0,identity_json TEXT NOT NULL DEFAULT "{}",last_observed_at INTEGER NOT NULL DEFAULT 0)')
   cols={row[1] for row in d.execute('PRAGMA table_info(devices)')}
   if 'active' not in cols:d.execute('ALTER TABLE devices ADD COLUMN active INTEGER NOT NULL DEFAULT 0')
   if 'identity_json' not in cols:d.execute('ALTER TABLE devices ADD COLUMN identity_json TEXT NOT NULL DEFAULT "{}"')
   if 'last_observed_at' not in cols:d.execute('ALTER TABLE devices ADD COLUMN last_observed_at INTEGER NOT NULL DEFAULT 0')
   d.execute('CREATE TABLE IF NOT EXISTS streams(id TEXT PRIMARY KEY,device_id TEXT NOT NULL,name TEXT NOT NULL,kind TEXT NOT NULL,port INTEGER NOT NULL,path TEXT NOT NULL,protocol TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1)')
 def _load(self):
  with self._connect() as d:
   rows=d.execute('SELECT id,name,type,host,port,connection,notes,active,identity_json,last_observed_at FROM devices ORDER BY name').fetchall();srows=d.execute('SELECT id,device_id,name,kind,port,path,protocol,enabled FROM streams ORDER BY name').fetchall()
  self._items=[];self._active=''
  for r in rows:
   try:identity=json.loads(r[8]) if r[8] else {}
   except ValueError:identity={}
   item={'id':r[0],'name':r[1],'type':r[2],'host':r[3],'port':r[4],'connection':r[5],'notes':r[6],'active':bool(r[7]),'openipcIdentity':identity,'lastObservedAt':r[9]};item.update(device_center_fields(item));self._items.append(item)
   if item['active']:self._active=item['id']
  self._items.sort(key=lambda item:(item['deviceGroup'],item['name'].casefold()))
  self._streams=[{'id':r[0],'device_id':r[1],'name':r[2],'kind':r[3],'port':r[4],'path':r[5],'protocol':r[6],'enabled':bool(r[7])} for r in srows]
 @Property('QVariantList',notify=changed)
 def items(self):return self._items
 @Property('QVariantList',notify=streamsChanged)
 def streams(self):return self._streams
 @Property('QVariantList',notify=streamsChanged)
 def activeStreams(self):return [x for x in self._streams if x['device_id']==self._active and x['enabled']]
 @Property(int,notify=changed)
 def count(self):return len(self._items)
 @Property(str,notify=changed)
 def activeName(self):return next((x['name'] for x in self._items if x['id']==self._active),'')
 @Property('QVariantList',notify=discoveryChanged)
 def discovered(self):return self._discovered
 @Property(bool,notify=discoveryChanged)
 def scanning(self):return self._scanning
 @Property(str,notify=discoveryChanged)
 def discoveryStage(self):return self._stage
 @Property(str,notify=discoveryChanged)
 def discoveryStatus(self):return self._status
 @Property(int,notify=discoveryChanged)
 def progressDone(self):return self._pd
 @Property(int,notify=discoveryChanged)
 def progressTotal(self):return self._pt
 @Property(int,notify=discoveryChanged)
 def foundCount(self):return self._found
 @Property('QVariantList',constant=True)
 def interfaces(self):return interfaces()
 @Slot(str,str,str,int,str,str,result=str)
 def addDevice(self,name,typ,host,port,connection,notes):
  if not name.strip() or not valid_host(host.strip()):return ''
  did=uuid.uuid4().hex
  with self._connect() as d:d.execute('INSERT INTO devices(id,name,type,host,port,connection,notes,active,identity_json) VALUES(?,?,?,?,?,?,?,?,?)',(did,name.strip(),typ,host.strip(),max(1,min(int(port),65535)),connection,notes.strip(),0,'{}'))
  self._load();self.changed.emit();self.deviceAdded.emit();return did
 @Slot(str)
 def removeDevice(self,did):
  existed=any(x.get('id')==did for x in self._items)
  with self._connect() as d:d.execute('DELETE FROM streams WHERE device_id=?',(did,));d.execute('DELETE FROM devices WHERE id=?',(did,))
  self._load();self.changed.emit();self.streamsChanged.emit()
  if existed:self.deviceRemoved.emit()
 @Slot(str)
 def setActive(self,did):
  if not any(x['id']==did for x in self._items):return
  with self._connect() as d:d.execute('UPDATE devices SET active=0');d.execute('UPDATE devices SET active=1 WHERE id=?',(did,))
  self._load();self.changed.emit();self.streamsChanged.emit()
 @Slot()
 def clearActive(self):
  with self._connect() as d:d.execute('UPDATE devices SET active=0')
  self._load();self.changed.emit();self.streamsChanged.emit()
 def _save_identity(self,did,identity):
  with self._connect() as d:d.execute('UPDATE devices SET identity_json=? WHERE id=?',(json.dumps(identity,ensure_ascii=False),did))
 @Slot(str,result=bool)
 def markObserved(self,host):
  address=str(host or '').strip()
  if not address:return False
  with self._connect() as d:changed=d.execute("UPDATE devices SET last_observed_at=strftime('%s','now') WHERE host=?",(address,)).rowcount
  if changed:self._load();self.changed.emit()
  return changed>0
 @Slot(str,str,str,int,str,str,result=str)
 def addStream(self,did,name,kind,port,path,protocol):
  if not any(x['id']==did for x in self._items):return ''
  sid=uuid.uuid4().hex
  with self._connect() as d:d.execute('INSERT INTO streams(id,device_id,name,kind,port,path,protocol,enabled) VALUES(?,?,?,?,?,?,?,1)',(sid,did,name.strip() or 'Відео',kind.strip() or 'main',max(1,min(int(port),65535)),path.strip() or '/',protocol.strip().lower() or 'rtsp'))
  self._load();self.streamsChanged.emit();return sid
 @Slot(str)
 def removeStream(self,sid):
  with self._connect() as d:d.execute('DELETE FROM streams WHERE id=?',(sid,))
  self._load();self.streamsChanged.emit()
 @Slot(str,bool)
 def setStreamEnabled(self,sid,enabled):
  with self._connect() as d:d.execute('UPDATE streams SET enabled=? WHERE id=?',(int(bool(enabled)),sid))
  self._load();self.streamsChanged.emit()
 @Slot(result='QVariantMap')
 def exportSnapshot(self):
  devices=[{k:x[k] for k in ('id','name','type','host','port','connection','notes')} for x in self._items]
  identities=[{'device_id':x['id'],**dict(x.get('openipcIdentity') or {})} for x in self._items if (x.get('openipcIdentity') or {}).get('verified')]
  return {'devices':devices,'streams':[dict(x) for x in self._streams],'videoProfiles':[],'openipcIdentities':identities,'activeDeviceId':self._active}
 @Slot('QVariantMap',result=bool)
 def validateSnapshot(self,value):
  if not isinstance(value,dict) or set(value)!={'devices','streams','videoProfiles','openipcIdentities','activeDeviceId'}:return False
  if not all(isinstance(value[k],list) for k in ('devices','streams','videoProfiles','openipcIdentities')) or not isinstance(value['activeDeviceId'],str):return False
  ids=[]
  for d in value['devices']:
   if not isinstance(d,dict) or set(d)!={'id','name','type','host','port','connection','notes'} or not d.get('id') or not d.get('name') or not valid_host(str(d.get('host',''))):return False
   ids.append(d['id'])
  if len(ids)!=len(set(ids)) or (value['activeDeviceId'] and value['activeDeviceId'] not in ids):return False
  stream_ids=[]
  for s in value['streams']:
   if not isinstance(s,dict) or s.get('device_id') not in ids or not s.get('id'):return False
   stream_ids.append(s['id'])
  if len(stream_ids)!=len(set(stream_ids)):return False
  return not any(not isinstance(i,dict) or i.get('device_id') not in ids or i.get('verified') is not True for i in value['openipcIdentities'])
 @Slot('QVariantMap',result=bool)
 def restoreSnapshot(self,value):
  if not self.validateSnapshot(value):return False
  try:
   with self._connect() as d:
    d.execute('BEGIN IMMEDIATE');d.execute('DELETE FROM streams');d.execute('DELETE FROM devices')
    for item in value['devices']:
     active=int(item['id']==value['activeDeviceId']);identity=next((x for x in value['openipcIdentities'] if x.get('device_id')==item['id']),{})
     d.execute('INSERT INTO devices(id,name,type,host,port,connection,notes,active,identity_json) VALUES(?,?,?,?,?,?,?,?,?)',(item['id'],item['name'],item['type'],item['host'],int(item['port']),item['connection'],item['notes'],active,json.dumps({k:v for k,v in identity.items() if k!='device_id'},ensure_ascii=False)))
    for s in value['streams']:d.execute('INSERT INTO streams(id,device_id,name,kind,port,path,protocol,enabled) VALUES(?,?,?,?,?,?,?,?)',(s['id'],s['device_id'],s['name'],s['kind'],int(s['port']),s['path'],s['protocol'],int(bool(s.get('enabled')))))
  except (sqlite3.Error,KeyError,TypeError,ValueError):return False
  self._load();self.changed.emit();self.streamsChanged.emit();self.deviceListRestored.emit();return True
 def snapshot(self):return {'devices':self._items,'streams':self._streams}
