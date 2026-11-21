from pathlib import Path
import unittest
class NavigationUiPolicyTests(unittest.TestCase):
 def setUp(self):
  here=Path(__file__).parent;self.main=(here/'Main.qml').read_text(encoding='utf-8');self.home=(here/'HomePanel.qml').read_text(encoding='utf-8');self.update=(here/'UpdatePanel.qml').read_text(encoding='utf-8')
 def test_home_exposes_required_entry_points(self):
  for label in ('Пристрої','Швидке підключення','Firmware','Оновлення','Діагностика'):self.assertIn(label,self.home)
 def test_quick_connect_uses_saved_devices_with_real_enabled_stream(self):
  self.assertIn('model:devicesModel.items',self.home);self.assertIn('devicesModel.streams',self.home);self.assertIn('streams[n].enabled===true',self.home);self.assertNotIn('discoverOpenIPC()',self.home)
 def test_quick_connect_does_not_claim_observed_connectivity(self):self.assertIn('не означає підтверджену мережеву доступність',self.home)
 def test_update_ui_uses_existing_guarded_updater_only(self):
  for call in ('updater.check()','updater.download()','updater.install()'):self.assertIn(call,self.update)
 def test_main_exposes_service_mode_without_fake_observers(self):
  self.assertIn('SERVICE MODE',self.main);self.assertNotIn('observeStabX',self.main);self.assertNotIn('observeStarlink',self.main)
 def test_navigation_stop_clears_media_sources(self):self.assertIn('player.source=""',self.main);self.assertIn('secondaryPlayer.source=""',self.main)
if __name__=='__main__':unittest.main()
