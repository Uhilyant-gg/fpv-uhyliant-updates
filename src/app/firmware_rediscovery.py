"""Post-upgrade rediscovery with bounded candidate expansion and identity continuity."""
import concurrent.futures,time
from openipc_device import normalize_openipc_identity

_FRESH_OPENIPC_EVIDENCE={'Majestic /api/v1/config.json','OpenIPC status.cgi'}
_MAX_REDISCOVERY_WORKERS=24

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
 def _matches(self,candidate,result,original,platform,sensor):
  identity=self._fresh_identity(result)
  if identity is None:return None
  if platform and sensor:
   if str(identity.get('platform','')).strip().lower()!=platform or str(identity.get('sensor','')).strip().lower()!=sensor:return None
  elif candidate!=original:return None
  return identity
 def _probe_one(self,candidate):
  try:return self.probe(candidate)
  except Exception:return None
 def wait(self,host,attempts=30,interval=2.0,expected_identity=None):
  attempts=max(1,min(int(attempts),120));interval=max(0.0,min(float(interval),10.0));expected=expected_identity if isinstance(expected_identity,dict) else {};platform=str(expected.get('platform','')).strip().lower();sensor=str(expected.get('sensor','')).strip().lower();hosts=self._hosts(host);original=str(host).strip()
  for index in range(attempts):
   direct=self._probe_one(original);identity=self._matches(original,direct,original,platform,sensor)
   if identity is not None:return {'rediscovered':True,'attempts':index+1,'host':original,'identity':identity}
   candidates=[candidate for candidate in hosts if candidate!=original]
   if platform and sensor and candidates:
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(_MAX_REDISCOVERY_WORKERS,len(candidates))) as pool:
     futures={pool.submit(self._probe_one,candidate):candidate for candidate in candidates}
     for future in concurrent.futures.as_completed(futures):
      candidate=futures[future]
      try:result=future.result()
      except Exception:result=None
      identity=self._matches(candidate,result,original,platform,sensor)
      if identity is not None:
       for pending in futures:pending.cancel()
       return {'rediscovered':True,'attempts':index+1,'host':candidate,'identity':identity}
   if index+1<attempts:self.sleep(interval)
  return {'rediscovered':False,'attempts':attempts,'host':'','identity':normalize_openipc_identity()}
