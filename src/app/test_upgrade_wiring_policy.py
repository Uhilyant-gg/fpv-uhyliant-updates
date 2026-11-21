import re,unittest
from pathlib import Path
class Tests(unittest.TestCase):
 def test_main_exposes_session_but_does_not_enable_destructive_transport(self):
  text=Path(__file__).with_name('main.py').read_text(encoding='utf-8')
  self.assertRegex(text,r'FirmwareUpdateSession\(fwexec,d(?:,events=diag_events)?\)')
  self.assertNotIn('AuthenticatedCameraTransport(',text);self.assertNotIn('ExistingSshTransport(',text);self.assertNotIn('configure_transport(',text)
 def test_no_host_key_bypass_or_plaintext_secret_flags(self):
  root=Path(__file__).parent;text='\n'.join(p.read_text(encoding='utf-8') for p in [root/'openipc_ssh_transport.py',root/'authenticated_camera_transport.py']);self.assertNotIn('StrictHostKeyChecking=no',text);self.assertNotIn('sshpass',text);self.assertNotIn('--password',text)
if __name__=='__main__':unittest.main()
