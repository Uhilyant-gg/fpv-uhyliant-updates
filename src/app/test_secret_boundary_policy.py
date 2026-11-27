import unittest
from pathlib import Path
class Tests(unittest.TestCase):
 def test_secret_names_do_not_enter_firmware_plans_or_executor_status(self):
  root=Path(__file__).parent
  for name in ('firmware_center.py','firmware_executor.py','firmware_update_lifecycle.py'):
   text=(root/name).read_text(encoding='utf-8').lower();self.assertNotIn('password',text);self.assertNotIn('secret',text)
 def test_session_does_not_retain_transport_or_credentials(self):
  text=Path(__file__).with_name('firmware_update_session.py').read_text(encoding='utf-8');self.assertNotIn('self._transport',text);self.assertNotIn('CameraCredentials',text);self.assertNotIn('.password',text)
 def test_password_transport_never_uses_subprocess_or_shell(self):
  text=Path(__file__).with_name('authenticated_camera_transport.py').read_text(encoding='utf-8');self.assertNotIn('subprocess',text);self.assertNotIn('shell=',text);self.assertNotIn('sshpass',text)
if __name__=='__main__':unittest.main()
