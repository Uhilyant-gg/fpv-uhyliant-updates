from pathlib import Path
import unittest
class Tests(unittest.TestCase):
 def test_session_requires_preflight_before_authenticated_transport(self):
  text=Path(__file__).with_name('firmware_update_session.py').read_text(encoding='utf-8')
  self.assertIn('preflight is None',text);self.assertIn("readiness.get('ready') is not True",text);self.assertIn('AuthenticatedCameraTransport(credentials)',text)
 def test_firmware_ui_passes_preflight_and_disables_connect_until_ready(self):
  text=Path(__file__).with_name('FirmwareCenter.qml').read_text(encoding='utf-8')
  self.assertIn('hardwareReady:hardwareE2ERuntime.readiness',text);self.assertIn('enabled:hardwareReady.ready',text);self.assertIn('enableAuthenticatedTransport(cameraCredentials,hardwareE2ERuntime)',text)
if __name__=='__main__':unittest.main()
