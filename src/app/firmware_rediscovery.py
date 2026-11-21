"""Post-upgrade rediscovery with bounded candidate expansion and identity continuity."""
import time
from openipc_device import normalize_openipc_identity

_FRESH_OPENIPC_EVIDENCE={'Majestic /api/v1/config.json','OpenIPC status.cgi'}

class FirmwareRediscovery:
 def __init__(self,probe,sleep=time.sleep,candidates=None):self.probe=probe;self.sleep=sleep;self.candidates=candidates
 def _hosts(self,original_host):
  hosts=[str(original_host).strip()]
  if callable(self.candidates):
   try:extra=self.candidates(original_host)
   except Exception:extra=()
   if isinstance(extra,(list,tuple)):
    for host in extra:
     value=str(host).strip()
     if value and value not in hosts:hosts.append(value)
  return hosts
 def _fresh_identity(self,result):
  if not isinstance(result,dict) or result.get('openipc') is not True:return None
  evidence=result.get('evidence');identity_data=result.get('identity')
  if not isinstance(evidence,(list,tuple)) or not isinstance(identity_data,dict):return None
  fresh=[item for item in evidence if isinstance(item,str) and item in _FRESH_OPENIPC_EVIDENCE]
  payload=dict(identity_data);payload['verified']=bool(fresh)
  identity=normalize_openipc_identity(payload,fresh)
  return identity if identity.get('verified') else None
 def wait(self,host,attempts=30,interval=2.0,expected_identity=None):
  attempts=max(1,min(int(attempts),120));interval=max(0.0,min(float(interval),10.0));expected=expected_identity if isinstance(expected_identity,dict) else {};platform=str(expected.get('platform','')).strip().lower();sensor=str(expected.get('sensor','')).strip().lower();hosts=self._hosts(host)
  for index in range(attempts):
   for candidate in hosts:
    try:result=self.probe(candidate)
    except Exception:result=None
    identity=self._fresh_identity(result)
    if identity is None:continue
    if platform and sensor:
     if str(identity.get('platform','')).strip().lower()!=platform or str(identity.get('sensor','')).strip().lower()!=sensor:continue
    elif candidate!=str(host).strip():continue
    return {'rediscovered':True,'attempts':index+1,'host':candidate,'identity':identity}
   if index+1<attempts:self.sleep(interval)
  return {'rediscovered':False,'attempts':attempts,'host':'','identity':normalize_openipc_identity()}
