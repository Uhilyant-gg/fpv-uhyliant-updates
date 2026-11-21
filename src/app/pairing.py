"""Station pairing trust metadata with a pluggable secret-store boundary.

Pairing starts software-side only: secrets are generated locally and never persisted by
this module unless an injected OS-protected store accepts them. Portable backup must
not include pairing state.
"""
import hashlib,secrets,time,uuid
from copy import deepcopy
from PySide6.QtCore import QObject, Property, Signal, Slot

class SecretStoreUnavailable(RuntimeError):pass

class SecretStore:
 """Interface for OS-protected pairing-secret storage."""
 available=False
 def put(self,key,value):raise SecretStoreUnavailable('OS-protected secret store unavailable')
 def delete(self,key):raise SecretStoreUnavailable('OS-protected secret store unavailable')

class PairingRegistry(QObject):
 changed=Signal()
 def __init__(self,secret_store=None,clock=None):
  super().__init__();self.store=secret_store or SecretStore();self.clock=clock or time.time;self._records={};self._pending={}
 @Property(bool,notify=changed)
 def secretStoreAvailable(self):return bool(getattr(self.store,'available',False))
 @Property('QVariantList',notify=changed)
 def trusted(self):return [deepcopy(v) for v in self._records.values()]
 @Property('QVariantList',notify=changed)
 def pending(self):return [deepcopy(v['public']) for v in self._pending.values()]
 def _fingerprint(self,secret):return hashlib.sha256(secret).hexdigest()
 @Slot(str,str,result='QVariantMap')
 def begin(self,label,endpoint):
  label=label.strip();endpoint=endpoint.strip()
  if not self.secretStoreAvailable or not label or not endpoint:return {}
  pid=uuid.uuid4().hex;secret=secrets.token_bytes(32);public={'id':pid,'label':label,'endpoint':endpoint,'fingerprint':self._fingerprint(secret),'createdAt':int(self.clock()),'state':'pending'};self._pending[pid]={'public':public,'secret':secret};self.changed.emit();return deepcopy(public)
 @Slot(str,bool,result=bool)
 def confirm(self,pairing_id,approved):
  item=self._pending.pop(pairing_id,None)
  if not item:self.changed.emit();return False
  if not approved:self.changed.emit();return False
  secret_key='pairing/'+pairing_id
  try:self.store.put(secret_key,item['secret'])
  except Exception:self.changed.emit();return False
  record={**item['public'],'state':'trusted','trustedAt':int(self.clock()),'secretRef':secret_key};self._records[pairing_id]=record;self.changed.emit();return True
 @Slot(str,result=bool)
 def revoke(self,pairing_id):
  record=self._records.get(pairing_id)
  if not record:return False
  try:self.store.delete(record['secretRef'])
  except Exception:return False
  self._records.pop(pairing_id,None);self.changed.emit();return True
 @Slot(str,result=bool)
 def cancel(self,pairing_id):
  existed=self._pending.pop(pairing_id,None) is not None
  if existed:self.changed.emit()
  return existed
 @Slot()
 def clearPending(self):self._pending.clear();self.changed.emit()
