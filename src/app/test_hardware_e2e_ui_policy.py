from pathlib import Path
import unittest
class Tests(unittest.TestCase):
 def setUp(self):
  root=Path(__file__).parent;self.qml=(root/'HardwareE2EPanel.qml').read_text(encoding='utf-8');self.main=(root/'Main.qml').read_text(encoding='utf-8');self.bootstrap=(root/'main.py').read_text(encoding='utf-8')
 def test_panel_exposes_preflight_without_destructive_execution(self):
  self.assertIn('hardwareE2ERuntime.readiness',self.qml);self.assertIn('exportPreflight()',self.qml);self.assertNotIn('firmwareUpdateSession.execute',self.qml);self.assertNotIn('sysupgrade',self.qml)
 def test_host_key_is_explicit_user_confirmation(self):self.assertIn('SSH host key перевірено та прийнято',self.qml);self.assertIn('setHostKeyAccepted(checked)',self.qml)
 def test_main_wires_preflight_panel_without_destructive_execution(self):
  self.assertIn('Hardware E2E',self.main);self.assertIn('HardwareE2EPanel',self.main);self.assertIn('hardwareE2EPopup.open()',self.main);self.assertIn('onOpened:hardwareE2ERuntime.reset()',self.main);self.assertIn('onClosed:hardwareE2ERuntime.reset()',self.main)
 def test_runtime_is_registered_in_application_context(self):
  self.assertIn('HardwareE2ERuntime(d,diag,credentials)',self.bootstrap);self.assertIn("('hardwareE2ERuntime',hardware_e2e)",self.bootstrap);self.assertIn('hardware_e2e.reset()',self.bootstrap)
 def test_panel_has_local_close_path(self):self.assertIn('signal closeRequested()',self.qml);self.assertIn('onClicked:closeRequested()',self.qml)
if __name__=='__main__':unittest.main()
