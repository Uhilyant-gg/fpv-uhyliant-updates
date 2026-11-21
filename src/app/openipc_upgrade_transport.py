"""Guarded authenticated transport boundary for an already-verified OpenIPC camera."""
from openipc_upgrade import UPGRADE_ARGV, upgrade_candidate

class OpenIPCUpgradeAdapter:
 def __init__(self,devices,transport):self.devices=devices;self.transport=transport
 def _device(self,did):return next((d for d in self.devices.items if d.get('id')==did),None)
 def execute(self,device_id,profile,mode,artifact,plan):
  if mode!='upgrade':return False
  initial=upgrade_candidate(self._device(device_id))
  if not initial.get('ready'):return False
  authenticate=getattr(self.transport,'authenticate',None)
  if authenticate is not None and not authenticate(initial['host']):return False
  # Re-read observed identity after authentication and immediately before the destructive command.
  current=self._device(device_id);ready=upgrade_candidate(current)
  if not ready.get('ready') or ready['host']!=initial['host'] or ready.get('platform')!=initial.get('platform') or ready.get('sensor')!=initial.get('sensor'):return False
  return bool(self.transport.run(ready['host'],list(UPGRADE_ARGV)))
