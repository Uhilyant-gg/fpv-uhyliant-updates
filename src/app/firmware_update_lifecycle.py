"""End-to-end post-dispatch OpenIPC update verification orchestration."""
from firmware_center import SUPPORTED_PROFILES
from firmware_rediscovery import _private_candidate
from post_flash_verify import verify_post_flash

class FirmwareUpdateLifecycle:
 def __init__(self,executor,rediscovery):self.executor=executor;self.rediscovery=rediscovery
 def verify_after_reboot(self,attempts=30,interval=2.0):
  started=self.executor.beginRediscovery()
  if not started:return False
  context,nonce=started;before=context.get('before') or {}
  if not _private_candidate(context.get('host','')):return self.executor.failRediscovery(nonce)
  if not str(before.get('platform','')).strip() or not str(before.get('sensor','')).strip():return self.executor.failRediscovery(nonce)
  try:result=self.rediscovery.wait(context['host'],attempts,interval,before)
  except Exception:return self.executor.failRediscovery(nonce)
  if not isinstance(result,dict) or result.get('rediscovered') is not True:return self.executor.failRediscovery(nonce)
  host=str(result.get('host','')).strip()
  if not _private_candidate(host):return self.executor.failRediscovery(nonce)
  profile=SUPPORTED_PROFILES.get(context['profile'])
  if not isinstance(profile,dict) or not profile:return self.executor.failRediscovery(nonce)
  try:verification=verify_post_flash(before,result.get('identity') or {},profile,context.get('expectedFirmware',''))
  except Exception:return self.executor.failRediscovery(nonce)
  verification['rediscoveredHost']=host
  verification['streams']=result.get('streams',[]) if isinstance(result.get('streams'),list) else []
  return self.executor.acceptRediscoveredVerification(result,verification,nonce)
