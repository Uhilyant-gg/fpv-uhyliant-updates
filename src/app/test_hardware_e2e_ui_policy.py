from pathlib import Path
import unittest
class Tests(unittest.TestCase):
 def setUp(self):self.qml=(Path(__file__).parent/'HardwareE2EPanel.qml').read_text(encoding='utf-8')
 def test_panel_exposes_preflight_without_destructive_execution(self):
  self.assertIn('hardwareE2ERuntime.readiness',self.qml);self.assertIn('exportPreflight()',self.qml);self.assertNotIn('firmwareUpdateSession.execute',self.qml);self.assertNotIn('sysupgrade',self.qml)
 def test_host_key_is_explicit_user_confirmation(self):self.assertIn('SSH host key перевірено та прийнято',self.qml);self.assertIn('setHostKeyAccepted(checked)',self.qml)
if __name__=='__main__':unittest.main()
