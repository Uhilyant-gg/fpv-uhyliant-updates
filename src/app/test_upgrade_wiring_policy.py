from pathlib import Path
import unittest
class Tests(unittest.TestCase):
 def test_main_does_not_silently_register_destructive_upgrade_transport(self):
  text=(Path(__file__).parent/'main.py').read_text(encoding='utf-8');self.assertNotIn('ExistingSshTransport(',text);self.assertNotIn('register_adapter(OpenIPCUpgradeAdapter',text)
 def test_no_host_key_bypass_or_plaintext_secret_flags(self):
  text=(Path(__file__).parent/'openipc_ssh_transport.py').read_text(encoding='utf-8');self.assertNotIn('StrictHostKeyChecking=no',text);self.assertNotIn('sshpass',text);self.assertNotIn('-p ',text)
if __name__=='__main__':unittest.main()
