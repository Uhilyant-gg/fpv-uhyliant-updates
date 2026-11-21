from pathlib import Path
import unittest
class NavigationUiPolicyTests(unittest.TestCase):
 def setUp(self):
  here=Path(__file__).parent;self.main=(here/'Main.qml').read_text(encoding='utf-8');self.home=(here/'HomePanel.qml').read_text(encoding='utf-8');self.update=(here/'UpdatePanel.qml').read_text(encoding='utf-8')
 def test_home_exposes_required_entry_points(self):
  for label in ('Пристрої','Швидке підключення','Firmware','Оновлення','Діагностика'):self.assertIn(label,self.home)
 def test_quick_connect_uses_saved_devices(self):self.assertIn('model:devicesModel.items',self.home);self.assertNotIn('discoverOpenIPC()',self.home)
 def test_update_ui_uses_existing_guarded_updater_only(self):
  for call in ('updater.check()','updater.download()','updater.install()'):self.assertIn(call,self.update)
 def test_main_exposes_service_mode_without_fake_observers(self):
  self.assertIn('SERVICE MODE',self.main);self.assertNotIn('observeStabX',self.main);self.assertNotIn('observeStarlink',self.main)
if __name__=='__main__':unittest.main()
