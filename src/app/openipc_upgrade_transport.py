"""Guarded authenticated transport boundary for an already-verified OpenIPC camera."""
from openipc_upgrade import UPGRADE_ARGV, upgrade_candidate

class OpenIPCUpgradeAdapter:
 def __init__(self,devices,transport):self.devices=devices;self.transport=transport
 def _device(self,did):return next((d for d in self.devices.items if d.get('id')==did),None)
 def execute(self,device_id,profile,mode,artifact,plan,handoff=None):
  if mode!='upgrade' or not isinstance(artifact,dict) or not isinstance(plan,dict) or not isinstance(handoff,dict):return False
  sha=str(artifact.get('sha256','')).lower();size=artifact.get('size')
  if not artifact.get('verified') or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha) or type(size) is not int or size<=0:return False
  if plan.get('ready') is not True or not plan.get('approvalToken') or plan.get('artifactSha256')!=sha or plan.get('artifactSize')!=size:return False
  if handoff.get('deviceId')!=device_id or handoff.get('profile')!=profile or handoff.get('mode')!=mode:return False
  if handoff.get('verifiedOpenIPC') is not True:return False
  if handoff.get('artifact')!=artifact or handoff.get('plan')!=plan:return False
  approval=handoff.get('approval')
  if not isinstance(approval,dict) or approval.get('deviceId')!=device_id or approval.get('profile')!=profile or approval.get('mode')!=mode:return False
  if approval.get('approvalToken')!=plan.get('approvalToken') or approval.get('artifactSha256')!=sha:return False
  initial=upgrade_candidate(self._device(device_id))
  if not initial.get('ready') or initial.get('host')!=handoff.get('host') or initial.get('platform')!=handoff.get('platform') or initial.get('sensor')!=handoff.get('sensor'):return False
  authenticate=getattr(self.transport,'authenticate',None)
  if not callable(authenticate) or not authenticate(initial['host']):return False
  current=self._device(device_id);ready=upgrade_candidate(current)
  if not ready.get('ready') or ready['host']!=handoff.get('host') or ready.get('platform')!=handoff.get('platform') or ready.get('sensor')!=handoff.get('sensor'):return False
  return bool(self.transport.run(ready['host'],list(UPGRADE_ARGV)))
