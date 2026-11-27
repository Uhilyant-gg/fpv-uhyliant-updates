"""Windows Credential Manager adapter for pairing secrets."""
from __future__ import annotations
import ctypes,sys
from ctypes import wintypes
from pairing import SecretStore,SecretStoreUnavailable
_CRED_TYPE_GENERIC=1
_CRED_PERSIST_LOCAL_MACHINE=2
_ERROR_NOT_FOUND=1168
_MAX_CREDENTIAL_BLOB_SIZE=5*512
class _CREDENTIALW(ctypes.Structure):
 _fields_=[('Flags',wintypes.DWORD),('Type',wintypes.DWORD),('TargetName',wintypes.LPWSTR),('Comment',wintypes.LPWSTR),('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),('Persist',wintypes.DWORD),('AttributeCount',wintypes.DWORD),('Attributes',ctypes.c_void_p),('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]
class _WinCredApi:
 def __init__(self):
  dll=ctypes.WinDLL('Advapi32.dll',use_last_error=True);self._write=dll.CredWriteW;self._write.argtypes=[ctypes.POINTER(_CREDENTIALW),wintypes.DWORD];self._write.restype=wintypes.BOOL;self._read=dll.CredReadW;self._read.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(_CREDENTIALW))];self._read.restype=wintypes.BOOL;self._delete=dll.CredDeleteW;self._delete.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD];self._delete.restype=wintypes.BOOL;self._free=dll.CredFree;self._free.argtypes=[ctypes.c_void_p];self._free.restype=None
 @staticmethod
 def _error(operation):raise SecretStoreUnavailable(f'Windows Credential Manager {operation} failed ({ctypes.get_last_error()})')
 def put(self,target,value):
  blob=(ctypes.c_ubyte*len(value)).from_buffer_copy(value);credential=_CREDENTIALW();credential.Type=_CRED_TYPE_GENERIC;credential.TargetName=target;credential.CredentialBlobSize=len(value);credential.CredentialBlob=ctypes.cast(blob,ctypes.POINTER(ctypes.c_ubyte));credential.Persist=_CRED_PERSIST_LOCAL_MACHINE;credential.UserName='FPV-Uhyliant'
  if not self._write(ctypes.byref(credential),0):self._error('write')
 def get(self,target):
  credential=ctypes.POINTER(_CREDENTIALW)()
  if not self._read(target,_CRED_TYPE_GENERIC,0,ctypes.byref(credential)):
   if ctypes.get_last_error()==_ERROR_NOT_FOUND:return None
   self._error('read')
  try:
   item=credential.contents
   return ctypes.string_at(item.CredentialBlob,item.CredentialBlobSize) if item.CredentialBlobSize else b''
  finally:self._free(credential)
 def delete(self,target):
  if self._delete(target,_CRED_TYPE_GENERIC,0):return
  if ctypes.get_last_error()!=_ERROR_NOT_FOUND:self._error('delete')
class WindowsCredentialSecretStore(SecretStore):
 """Current-user protected pairing storage. Real Windows validation is pending."""
 def __init__(self,api=None,platform=None,target_prefix='FPV-Uhyliant/'):
  platform=sys.platform if platform is None else platform;self._api=api;self._prefix=target_prefix;self.available=False;self.validation_pending=platform=='win32';self.error=''
  if platform!='win32':self.error='Windows Credential Manager is only available on Windows';return
  try:self._api=self._api or _WinCredApi();self.available=True
  except Exception as exc:self.error=str(exc)
 def _target(self,key):
  if not isinstance(key,str) or not any(key.startswith(prefix) and len(key)>len(prefix) for prefix in ('pairing/','backup/')):raise SecretStoreUnavailable('invalid secret key')
  return self._prefix+key
 def put(self,key,value):
  if not self.available:raise SecretStoreUnavailable(self.error or 'Windows Credential Manager unavailable')
  secret=bytes(value)
  if not secret or len(secret)>_MAX_CREDENTIAL_BLOB_SIZE:raise SecretStoreUnavailable('invalid pairing secret size')
  self._api.put(self._target(key),secret)
 def get(self,key):
  if not self.available:raise SecretStoreUnavailable(self.error or 'Windows Credential Manager unavailable')
  return self._api.get(self._target(key))
 def delete(self,key):
  if not self.available:raise SecretStoreUnavailable(self.error or 'Windows Credential Manager unavailable')
  self._api.delete(self._target(key))
 def contains(self,key):return self.get(key) is not None
