"""Guarded transport boundary for an already-verified OpenIPC camera.

No credentials are stored here. The injected transport owns authentication.
The command is a fixed argv tuple, never constructed from user input.
"""
from openipc_upgrade import UPGRADE_ARGV, upgrade_candidate

class OpenIPCUpgradeAdapter:
 def __init__(self,devices,transport):self.devices=devices;self.transport=transport
 def _device(self,did):return next((d for d in self.devices.items if d.get('id')==did),None)
 def execute(self,device_id,profile,mode,artifact,plan):
  if mode!='upgrade':return False
  device=self._device(device_id);ready=upgrade_candidate(device)
  if not ready.get('ready'):return False
  # The normal online upgrade deliberately ignores a local image artifact. The
  # existing FirmwareExecutor still guards handoff integrity for legacy modes.
  return bool(self.transport.run(ready['host'],list(UPGRADE_ARGV)))
