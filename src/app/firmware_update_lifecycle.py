"""End-to-end post-dispatch OpenIPC update verification orchestration."""
from firmware_center import SUPPORTED_PROFILES
from post_flash_verify import verify_post_flash

class FirmwareUpdateLifecycle:
 def __init__(self,executor,rediscovery):self.executor=executor;self.rediscovery=rediscovery
 def verify_after_reboot(self,attempts=30,interval=2.0):
  started=self.executor.beginRediscovery()
  if not started:return False
  context,nonce=started
  try:result=self.rediscovery.wait(context['host'],attempts,interval,context['before'])
  except Exception:return self.executor.failRediscovery(nonce)
  if not isinstance(result,dict) or result.get('rediscovered') is not True:return self.executor.failRediscovery(nonce)
  profile=SUPPORTED_PROFILES.get(context['profile'])
  if not isinstance(profile,dict) or not profile:return self.executor.failRediscovery(nonce)
  try:verification=verify_post_flash(context['before'],result.get('identity') or {},profile,'')
  except Exception:return self.executor.failRediscovery(nonce)
  verification['rediscoveredHost']=str(result.get('host',''))
  return self.executor.acceptRediscoveredVerification(result,verification,nonce)
