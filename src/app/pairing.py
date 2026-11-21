"""Station pairing trust lifecycle with secret-store and metadata-store boundaries."""
import hashlib,secrets,time,uuid
from copy import deepcopy
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

class PairingRegistry(QObject):
 changed=Signal()
 def __init__(self,secret_store=None,metadata_store=None,clock=None):
  super().__init__();self.store=secret_store or SecretStore();self.metadata=metadata_store or MetadataStore();self.clock=clock or time.time;self._records={};self._pending={};self._load()
 def _load(self):
  if not getattr(self.metadata,'available',False):return
  try:
   records=self.metadata.load();self._records={r['id']:dict(r) for r in records if self._valid_record(r)}
  except Exception:self._records={}
 def _valid_record(self,r):
  required={'id','label','endpoint','fingerprint','createdAt','trustedAt','state','secretRef'}
  return isinstance(r,dict) and set(r)==required and all(isinstance(r.get(k),str) for k in ('id','label','endpoint','fingerprint','state','secretRef')) and r.get('state')=='trusted' and isinstance(r.get('createdAt'),int) and isinstance(r.get('trustedAt'),int) and len(r.get('fingerprint',''))==64
 def _persist(self,records):
  if not getattr(self.metadata,'available',False):return False
  try:self.metadata.save([deepcopy(v) for v in records.values()]);return True
  except Exception:return False
 @Property(bool,notify=changed)
 def secretStoreAvailable(self):return bool(getattr(self.store,'available',False))
 @Property(bool,notify=changed)
 def metadataStoreAvailable(self):return bool(getattr(self.metadata,'available',False))
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
  item=self._pending.pop(pairing_id,None)
  if not item or not approved:self.changed.emit();return False
  secret_key='pairing/'+pairing_id
  try:self.store.put(secret_key,item['secret'])
  except Exception:self.changed.emit();return False
  record={**item['public'],'state':'trusted','trustedAt':int(self.clock()),'secretRef':secret_key};candidate={**self._records,pairing_id:record}
  if not self._persist(candidate):
   try:self.store.delete(secret_key)
   except Exception:pass
   self.changed.emit();return False
  self._records=candidate;self.changed.emit();return True
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
  if not self.secretStoreAvailable:return
  changed=False
  for pid,record in list(self._records.items()):
   try:present=self.store.contains(record['secretRef'])
   except Exception:continue
   if not present:self._records.pop(pid,None);changed=True
  if changed:self._persist(self._records);self.changed.emit()
