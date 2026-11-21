"""Encrypted, versioned station backups with explicit transactional restore."""
import base64,hashlib,hmac,json,os,secrets
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot
SCHEMA='fpv-uhyliant-station-backup';VERSION=2;KDF='scrypt';CIPHER='hmac-sha256-stream-v1';N=16384;R=8;P=1

def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def _b64(value):return base64.b64encode(value).decode('ascii')
def _unb64(value):return base64.b64decode(value.encode('ascii'),validate=True)
def _derive(password,salt):return hashlib.scrypt(password.encode('utf-8'),salt=salt,n=N,r=R,p=P,dklen=64)
def _stream(key,nonce,size):
 out=bytearray();counter=0
 while len(out)<size:out.extend(hmac.new(key,nonce+counter.to_bytes(8,'big'),hashlib.sha256).digest());counter+=1
 return bytes(out[:size])
def _seal(payload,password):
 salt=secrets.token_bytes(16);nonce=secrets.token_bytes(16);enc,mac=_derive(password,salt)[:32],_derive(password,salt)[32:];plain=_json(payload);cipher=bytes(a^b for a,b in zip(plain,_stream(enc,nonce,len(plain))));header={'schema':SCHEMA,'version':VERSION,'kdf':KDF,'cipher':CIPHER,'scrypt':{'n':N,'r':R,'p':P},'salt':_b64(salt),'nonce':_b64(nonce),'ciphertext':_b64(cipher)};header['mac']=hmac.new(mac,_json(header),hashlib.sha256).hexdigest();return header
def _open(wrapper,password):
 if not isinstance(wrapper,dict) or wrapper.get('schema')!=SCHEMA or wrapper.get('version')!=VERSION or wrapper.get('kdf')!=KDF or wrapper.get('cipher')!=CIPHER or wrapper.get('scrypt')!={'n':N,'r':R,'p':P}:raise ValueError('unsupported backup envelope')
 salt,nonce,cipher=_unb64(wrapper['salt']),_unb64(wrapper['nonce']),_unb64(wrapper['ciphertext']);enc,mac=_derive(password,salt)[:32],_derive(password,salt)[32:];signed={k:v for k,v in wrapper.items() if k!='mac'}
 if not hmac.compare_digest(str(wrapper.get('mac','')),hmac.new(mac,_json(signed),hashlib.sha256).hexdigest()):raise ValueError('backup authentication failed')
 return json.loads(bytes(a^b for a,b in zip(cipher,_stream(enc,nonce,len(cipher)))).decode('utf-8'))

class StationBackup(QObject):
 changed=Signal()
 def __init__(self,devices):super().__init__();self.devices=devices;self._result={'ready':False,'reason':'Backup operation not started','manifest':{}};self._pending=None;self._pending_path=''
 @Property('QVariantMap',notify=changed)
 def result(self):return dict(self._result)
 def _payload(self):return {'schema':SCHEMA,'version':VERSION,'devices':self.devices.exportSnapshot()}
 def _set(self,ready,reason,manifest=None):self._result={'ready':bool(ready),'reason':reason,'manifest':dict(manifest or {})};self.changed.emit()
 @Slot(str,str,result=bool)
 def exportEncrypted(self,path,password):
  if len(password)<8:self._set(False,'Backup password must contain at least 8 characters');return False
  try:
   target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);wrapper=_seal(self._payload(),password);temp=target.with_suffix(target.suffix+'.tmp');temp.write_text(json.dumps(wrapper,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,target);self._set(True,'Encrypted backup exported',{'schema':SCHEMA,'version':VERSION,'encrypted':True});return True
  except (OSError,TypeError,ValueError) as exc:self._set(False,'Backup export failed: '+str(exc));return False
 @Slot(str,str,result='QVariantMap')
 def inspectEncryptedImport(self,path,password):
  self._pending=None;self._pending_path=''
  try:
   payload=_open(json.loads(Path(path).read_text(encoding='utf-8')),password);valid=bool(payload.get('schema')==SCHEMA and payload.get('version')==VERSION and self.devices.validateSnapshot(payload.get('devices')))
   if not valid:self._set(False,'Backup payload is invalid or incompatible');return {}
   self._pending=payload['devices'];self._pending_path=str(Path(path).resolve());plan={'schema':SCHEMA,'version':VERSION,'encrypted':True,'deviceCount':len(self._pending['devices']),'execution':'explicit-confirmation-required'};self._set(True,'Restore plan verified; live data unchanged',plan);return dict(plan)
  except (OSError,TypeError,ValueError,KeyError,json.JSONDecodeError):self._set(False,'Backup authentication, compatibility, or read verification failed');return {}
 @Slot(bool,result=bool)
 def restoreInspected(self,confirmed):
  if not confirmed or self._pending is None:self._set(False,'Restore requires explicit confirmation and a verified import plan');return False
  snapshot=self._pending;self._pending=None;self._pending_path=''
  if not self.devices.restoreSnapshot(snapshot):self._set(False,'Transactional restore failed; live state preserved');return False
  self._set(True,'Transactional restore completed',{'schema':SCHEMA,'version':VERSION,'restored':True});return True
 @Slot()
 def cancelRestore(self):self._pending=None;self._pending_path='';self._set(False,'Restore plan cleared')
