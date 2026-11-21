from pathlib import Path
import re,unittest
class NavigationUiPolicyTests(unittest.TestCase):
 def setUp(self):
  here=Path(__file__).parent;self.main=(here/'Main.qml').read_text(encoding='utf-8');self.home=(here/'HomePanel.qml').read_text(encoding='utf-8');self.devices=(here/'DevicesPanel.qml').read_text(encoding='utf-8');self.update=(here/'UpdatePanel.qml').read_text(encoding='utf-8');self.hint=(here/'HoverHint.qml').read_text(encoding='utf-8')
 def test_home_has_single_camera_management_entry(self):
  self.assertEqual(self.home.count('onClicked:root.openDevices()'),1);self.assertIn('Знайти / додати',self.home);self.assertNotIn('Швидке підключення',self.home);self.assertNotIn('Popup{id:quick',self.home)
 def test_home_keeps_secondary_app_entry_points_compact(self):
  for label in ('Прошивка','Оновлення','Діагностика'):self.assertIn(label,self.home)
  self.assertNotIn('Пристрої · Додати камеру',self.home);self.assertNotIn('Відео передусім',self.home)
 def test_saved_camera_rows_are_direct_fpv_entry(self):
  self.assertIn('model:devicesModel.items',self.home);self.assertIn('devicesModel.streams',self.home);self.assertIn('streams[n].enabled===true',self.home);self.assertIn('root.connectDevice(modelData.id)',self.home)
 def test_devices_activation_uses_unified_fpv_handoff(self):
  self.assertIn('signal activateDevice(string deviceId)',self.devices);self.assertIn('root.activateDevice(selectedSaved.id)',self.devices);self.assertNotIn('onClicked:devicesModel.setActive(selectedSaved.id)',self.devices);self.assertIn('onActivateDevice:function(deviceId){devices.close();connectDevice(deviceId)}',self.main)
 def test_update_ui_uses_existing_guarded_updater_only(self):
  for call in ('updater.check()','updater.download()','updater.install()'):self.assertIn(call,self.update)
 def test_service_mode_does_not_duplicate_navigation_grid(self):
  self.assertIn('СЕРВІСНИЙ РЕЖИМ',self.main);self.assertNotIn('GridLayout{Layout.fillWidth:true;columns:4',self.main)
 def test_main_localizes_core_visible_surfaces(self):
  for text in ('ВІДЕО','Основний','Додатковий','Поміняти місцями','Телеметрія:','Мережа:','недоступно'):self.assertIn(text,self.main)
 def test_navigation_stop_clears_media_sources(self):self.assertIn('player.source=""',self.main);self.assertIn('secondaryPlayer.source=""',self.main)
 def test_hover_help_delay_is_five_seconds(self):self.assertIn('property int delay:5000',self.hint);self.assertIn('showTimer.restart()',self.hint)
 def test_compact_home_still_has_delayed_help(self):self.assertGreaterEqual(self.home.count('HoverHint{'),5)
if __name__=='__main__':unittest.main()
