import unittest
from pathlib import Path
class Tests(unittest.TestCase):
 def setUp(self):self.root=Path(__file__).parent
 def test_variant_is_never_inferred_or_hardcoded(self):
  for name in ('route_discovery.py','openipc_upgrade.py','post_flash_verify.py','firmware_update_lifecycle.py'):
   text=(self.root/name).read_text(encoding='utf-8').lower();self.assertNotIn('ultimate',text);self.assertNotIn('lite',text)
 def test_recovery_and_fullflash_are_not_normal_upgrade_commands(self):
  text=(self.root/'openipc_upgrade.py').read_text(encoding='utf-8');self.assertIn('UPGRADE_ARGV=("sysupgrade","-k","-r")',text);self.assertNotIn('fullflash',text.lower())
 def test_only_lifecycle_can_accept_post_reboot_verification(self):
  executor=(self.root/'firmware_executor.py').read_text(encoding='utf-8');session=(self.root/'firmware_update_session.py').read_text(encoding='utf-8');self.assertNotIn('verifyObserved',executor);self.assertNotIn('completeVerification',executor);self.assertIn('FirmwareUpdateLifecycle',session)
 def test_application_startup_keeps_destructive_transport_disabled(self):
  text=(self.root/'main.py').read_text(encoding='utf-8');self.assertNotIn('AuthenticatedCameraTransport(',text);self.assertNotIn('ExistingSshTransport(',text);self.assertNotIn('configure_transport(',text)
if __name__=='__main__':unittest.main()
