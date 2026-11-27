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
 def test_acquisition_executor_and_session_remain_separate_boundaries(self):
  acquisition=(self.root/'openipc_firmware_acquisition.py').read_text(encoding='utf-8');executor=(self.root/'firmware_executor.py').read_text(encoding='utf-8');session=(self.root/'firmware_update_session.py').read_text(encoding='utf-8')
  self.assertIn('self.center.verifyImage(',acquisition);self.assertNotIn('sysupgrade',acquisition.lower());self.assertNotIn('urllib.request',executor);self.assertNotIn('downloadSelected',executor);self.assertIn('OpenIPCUpgradeAdapter',session);self.assertIn('FirmwareRediscovery',session)
 def test_post_reboot_success_requires_observed_firmware(self):
  verifier=(self.root/'post_flash_verify.py').read_text(encoding='utf-8');lifecycle=(self.root/'firmware_update_lifecycle.py').read_text(encoding='utf-8')
  self.assertIn('bool(observed_firmware)',verifier);self.assertIn("result.get('identity')",lifecycle);self.assertNotIn("expected_firmware=context",lifecycle)
 def test_rediscovery_requires_fresh_openipc_evidence_and_identity_match(self):
  text=(self.root/'firmware_rediscovery.py').read_text(encoding='utf-8')
  self.assertIn("result.get('openipc') is not True",text);self.assertIn('_FRESH_OPENIPC_EVIDENCE',text);self.assertIn("identity.get('platform','')",text);self.assertIn("identity.get('sensor','')",text)
 def test_normal_upgrade_transport_revalidates_after_authentication(self):
  text=(self.root/'openipc_upgrade_transport.py').read_text(encoding='utf-8')
  auth=text.index("authenticate(initial['host'])");revalidate=text.index('current=self._device(device_id)',auth);run=text.index('self.transport.run(',revalidate);self.assertLess(auth,revalidate);self.assertLess(revalidate,run)
if __name__=='__main__':unittest.main()
