"""Post-upgrade rediscovery helper; acquisition is injectable and testable."""
import time
from openipc_device import normalize_openipc_identity

class FirmwareRediscovery:
 def __init__(self,probe,sleep=time.sleep):self.probe=probe;self.sleep=sleep
 def wait(self,host,attempts=30,interval=2.0):
  attempts=max(1,min(int(attempts),120));interval=max(0.0,min(float(interval),10.0))
  for index in range(attempts):
   result=self.probe(host)
   if result and result.get('openipc'):
    identity=normalize_openipc_identity(result.get('identity',{}),result.get('evidence',[]))
    if identity.get('verified'):return {'rediscovered':True,'attempts':index+1,'identity':identity}
   if index+1<attempts:self.sleep(interval)
  return {'rediscovered':False,'attempts':attempts,'identity':normalize_openipc_identity()}
