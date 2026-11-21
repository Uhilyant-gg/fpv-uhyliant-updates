"""Post-upgrade rediscovery helper; acquisition is injectable and testable."""
import time
from openipc_device import normalize_openipc_identity

_FRESH_OPENIPC_EVIDENCE={'Majestic /api/v1/config.json','OpenIPC status.cgi'}

class FirmwareRediscovery:
 def __init__(self,probe,sleep=time.sleep):self.probe=probe;self.sleep=sleep
 def wait(self,host,attempts=30,interval=2.0):
  attempts=max(1,min(int(attempts),120));interval=max(0.0,min(float(interval),10.0))
  for index in range(attempts):
   try:result=self.probe(host)
   except Exception:result=None
   if isinstance(result,dict) and result.get('openipc') is True:
    evidence=result.get('evidence');identity_data=result.get('identity')
    if isinstance(evidence,(list,tuple)) and isinstance(identity_data,dict):
     fresh_evidence=[item for item in evidence if isinstance(item,str) and item in _FRESH_OPENIPC_EVIDENCE]
     payload=dict(identity_data);payload['verified']=bool(fresh_evidence)
     identity=normalize_openipc_identity(payload,fresh_evidence)
     if identity.get('verified'):return {'rediscovered':True,'attempts':index+1,'identity':identity}
   if index+1<attempts:self.sleep(interval)
  return {'rediscovered':False,'attempts':attempts,'identity':normalize_openipc_identity()}
