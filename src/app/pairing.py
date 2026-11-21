"""Station pairing trust lifecycle with secret-store and durable metadata boundaries."""
import hashlib,json,os,secrets,time,uuid
from copy import deepcopy
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot

class SecretStoreUnavailable(RuntimeError):pass
class MetadataStoreUnavailable(RuntimeError):pass

class SecretStore:
 available=False
 def put(self,key,value):raise SecretStoreUnavailable('OS-protected secret store unavailable')
 def delete(self,key):raise SecretStoreUnavailable('OS-protected secret store unavailable')
 def contains(self,key):raise SecretStoreUnavailable('OS-protected secret store unavailable')

class MetadataStore:
 available=False
 def load(self):raise MetadataStoreUnavailable('pairing metadata store unavailable')
 def save(self,records):raise MetadataStoreUnavailable('pairing metadata store unavailable')

class JsonMetadataStore(MetadataStore):
 """Atomic non-secret trust metadata persistence. Never stores pairing secret bytes."""
 available=True
 def __init__(self,path):self.path=Path(path)
 def load(self):
  if not self.path.exists():return []
  raw=json.loads(self.path.read_text(encoding='utf-8'))
  if not isinstance(raw,dict) or set(raw)!={'schema','version','records'} or raw['schema']!='fpv-uhyliant-pairing-metadata' or raw['version']!=1 or not isinstance(raw['records'],list):raise MetadataStoreUnavailable('invalid pairing metadata')
  return [dict(r) for r in raw['records']]
 def save(self,records):
  self.path.parent.mkdir(parents=True,exist_ok=True);payload={'schema':'fpv-uhyliant-pairing-metadata','version':1,'records':[dict(r) for r in records]};tmp=self.path.with_suffix(self.path.suffix+'.tmp');tmp.write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')),encoding='utf-8');os.replace(tmp,self.path)

class PairingRegistry(QObject):
 changed=Signal()
 def __init__(self,secret_store=None,metadata_store=None,clock=None):
  super().__init__();self.store=secret_store or SecretStore();self.metadata=metadata_store or MetadataStore();self.clock=clock or time.time;self._records={};self._pending={};self._metadata_error='';self._load()
 def _load(self):
  if not getattr(self.metadata,'available',False):return
  try:
   records=self.metadata.load()
   if not all(self._valid_record(r) for r in records):raise MetadataStoreUnavailable('invalid trust record')
   self._records={r['id']:dict(r) for r in records};self._metadata_error=''
  except Exception as e:self._records={};self._metadata_error=str(e)
 def _valid_record(self,r):
  required={'id','label','endpoint','fingerprint','createdAt','trustedAt','state','secretRef'}
  return isinstance(r,dict) and set(r)==required and all(isinstance(r.get(k),str) and r.get(k) for k in ('id','label','endpoint','fingerprint','state','secretRef')) and r.get('state')=='trusted' and isinstance(r.get('createdAt'),int) and not isinstance(r.get('createdAt'),bool) and isinstance(r.get('trustedAt'),int) and not isinstance(r.get('trustedAt'),bool) and len(r.get('fingerprint',''))==64 and all(c in '0123456789abcdef' for c in r['fingerprint']) and r['secretRef']=='pairing/'+r['id']
 def _persist(self,records):
  if not getattr(self.metadata,'available',False):return False
  try:self.metadata.save([deepcopy(v) for v in records.values()]);self._metadata_error='';return True
  except Exception as e:self._metadata_error=str(e);return False
 @Property(bool,notify=changed)
 def secretStoreAvailable(self):return bool(getattr(self.store,'available',False))
 @Property(bool,notify=changed)
 def metadataStoreAvailable(self):return bool(getattr(self.metadata,'available',False)) and not self._metadata_error
 @Property(str,notify=changed)
 def metadataError(self):return self._metadata_error
 @Property('QVariantList',notify=changed)
 def trusted(self):return [deepcopy(v) for v in self._records.values()]
 @Property('QVariantList',notify=changed)
 def pending(self):return [deepcopy(v['public']) for v in self._pending.values()]
 def _fingerprint(self,secret):return hashlib.sha256(secret).hexdigest()
 @Slot(str,str,result='QVariantMap')
 def begin(self,label,endpoint):
  label=label.strip();endpoint=endpoint.strip()
  if not self.secretStoreAvailable or not self.metadataStoreAvailable or not label or not endpoint:return {}
  pid=uuid.uuid4().hex;secret=secrets.token_bytes(32);public={'id':pid,'label':label,'endpoint':endpoint,'fingerprint':self._fingerprint(secret),'createdAt':int(self.clock()),'state':'pending'};self._pending[pid]={'public':public,'secret':secret};self.changed.emit();return deepcopy(public)
 @Slot(str,bool,result=bool)
 def confirm(self,pairing_id,approved):
  item=self._pending.get(pairing_id)
  if not item or not approved:
   if item:self._pending.pop(pairing_id,None);self.changed.emit()
   return False
  secret_key='pairing/'+pairing_id
  try:self.store.put(secret_key,item['secret'])
  except Exception:return False
  record={**item['public'],'state':'trusted','trustedAt':int(self.clock()),'secretRef':secret_key};candidate={**self._records,pairing_id:record}
  if not self._persist(candidate):
   try:self.store.delete(secret_key)
   except Exception:pass
   return False
  self._pending.pop(pairing_id,None);self._records=candidate;self.changed.emit();return True
 @Slot(str,result=bool)
 def revoke(self,pairing_id):
  record=self._records.get(pairing_id)
  if not record:return False
  try:self.store.delete(record['secretRef'])
  except Exception:return False
  candidate=dict(self._records);candidate.pop(pairing_id,None)
  if not self._persist(candidate):return False
  self._records=candidate;self.changed.emit();return True
 @Slot(str,result=bool)
 def cancel(self,pairing_id):
  existed=self._pending.pop(pairing_id,None) is not None
  if existed:self.changed.emit()
  return existed
 @Slot()
 def clearPending(self):self._pending.clear();self.changed.emit()
 @Slot()
 def reconcile(self):
  if not self.secretStoreAvailable or not self.metadataStoreAvailable:return
  candidate=dict(self._records);changed=False
  for pid,record in list(candidate.items()):
   try:present=self.store.contains(record['secretRef'])
   except Exception:return
   if not present:candidate.pop(pid,None);changed=True
  if changed and self._persist(candidate):self._records=candidate;self.changed.emit()
