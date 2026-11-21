"""End-to-end post-dispatch OpenIPC update verification orchestration."""
from firmware_center import SUPPORTED_PROFILES
from post_flash_verify import verify_post_flash

class FirmwareUpdateLifecycle:
 def __init__(self,executor,rediscovery):self.executor=executor;self.rediscovery=rediscovery
 def verify_after_reboot(self,attempts=30,interval=2.0):
  context=self.executor.verificationContext()
  if not context.get('ready'):return False
  result=self.rediscovery.wait(context['host'],attempts,interval)
  if not result.get('rediscovered'):return self.executor.failRediscovery()
  profile=SUPPORTED_PROFILES.get(context['profile'],{})
  verification=verify_post_flash(context['before'],result.get('identity') or {},profile,'')
  return self.executor.acceptRediscoveredVerification(result,verification)
