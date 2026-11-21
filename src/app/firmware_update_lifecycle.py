"""End-to-end post-dispatch OpenIPC update verification orchestration."""
from firmware_center import SUPPORTED_PROFILES
from post_flash_verify import verify_post_flash

class FirmwareUpdateLifecycle:
 def __init__(self,executor,rediscovery):self.executor=executor;self.rediscovery=rediscovery
 def verify_after_reboot(self,attempts=30,interval=2.0):
  context=self.executor.beginRediscovery()
  if not context:return False
  try:result=self.rediscovery.wait(context['host'],attempts,interval)
  except Exception:return self.executor.failRediscovery()
  if not isinstance(result,dict) or result.get('rediscovered') is not True:return self.executor.failRediscovery()
  profile=SUPPORTED_PROFILES.get(context['profile'])
  if not isinstance(profile,dict) or not profile:return self.executor.failRediscovery()
  try:verification=verify_post_flash(context['before'],result.get('identity') or {},profile,'')
  except Exception:return self.executor.failRediscovery()
  return self.executor.acceptRediscoveredVerification(result,verification)
