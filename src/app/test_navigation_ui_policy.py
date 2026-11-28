import re
from pathlib import Path
import unittest


class NavigationUiPolicyTests(unittest.TestCase):
    def setUp(self):
        here = Path(__file__).parent
        self.main = (here / 'Main.qml').read_text(encoding='utf-8')
        self.home = (here / 'HomePanel.qml').read_text(encoding='utf-8')
        self.devices = (here / 'DevicesPanel.qml').read_text(encoding='utf-8')
        self.update = (here / 'UpdatePanel.qml').read_text(encoding='utf-8')
        self.hint = (here / 'HoverHint.qml').read_text(encoding='utf-8')

    def test_home_has_single_camera_management_entry(self):
        self.assertEqual(self.home.count('action: "devices"'), 1)
        self.assertIn('Камери', self.home)
        self.assertNotIn('Швидке підключення', self.home)
        self.assertNotIn('Popup{id:quick', self.home)
        self.assertIn('action: "devices"', self.home)

    def test_home_keeps_secondary_app_entry_points_compact(self):
        for label in ('Дрони і пресети', 'Налаштування станції', 'Обслуговування', 'Підготовка', 'Симуляція'):
            self.assertIn(label, self.home)
        for label in ('прошивка камери', 'резервна копія', 'Діагностика'):
            self.assertIn(label, self.home)
        self.assertIn('НАЗЕМНА СТАНЦІЯ', self.home)
        self.assertIn('Встановити ', self.home)
        header = self.home.split('НАЗЕМНА СТАНЦІЯ', 1)[1].split('МОЇ КАМЕРИ', 1)[0]
        self.assertIn('objectName: "homeUpdate"', header, 'update button sits next to the build version')
        self.assertNotIn('key:"update"', self.main)
        self.assertIn('visible: updater.updateState === "available" || updater.updateState === "ready"', self.home)
        self.assertNotIn('Button{text:"Оновлення"', self.home)
        self.assertNotIn('Пристрої · Додати камеру', self.home)
        self.assertNotIn('Відео передусім', self.home)

    def test_home_checks_for_updates_and_routes_contextual_action_to_guarded_ui(self):
        self.assertIn('Component.onCompleted: updater.check()', self.home)
        self.assertIn('onClicked: root.openUpdate()', self.home)

    def test_home_exposes_encrypted_backup_and_restore(self):
        self.assertIn('signal openBackup()', self.home)
        self.assertIn('резервна копія', self.home)
        self.assertIn('onOpenBackup:w.openStationSettings("backup")', self.main)
        self.assertIn('{key:"backup",label:"Резервна копія"', self.main)
        self.assertIn('Component{id:backupPage;BackupPanel{}}', self.main)

    def test_saved_camera_rows_are_direct_fpv_entry(self):
        self.assertIn('model: devicesModel.homeItems', self.home)
        self.assertIn('devicesModel.items.length', self.home)
        self.assertIn('item.onboardingState!=="ready"', self.main)
        self.assertIn('devicesModel.streams.length', self.home)
        self.assertIn('enabled === true', self.home)
        self.assertIn('root.connectDevice(modelData.id)', self.home)

    def test_devices_activation_uses_unified_fpv_handoff(self):
        self.assertIn('signal activateDevice(string deviceId)', self.devices)
        self.assertIn('root.activateDevice(selectedSaved.id)', self.devices)
        self.assertNotIn('onClicked:devicesModel.setActive(selectedSaved.id)', self.devices)
        self.assertIn('onActivateDevice:function(deviceId){devices.close();connectDevice(deviceId)}', self.main)

    def test_playback_rebuild_preserves_requested_pip(self):
        self.assertIn('var keepPip=pipEnabled&&streamWorkspace.state.pipAvailable', self.main)
        self.assertIn('videoWorkspaceRuntime.setPipEnabled(true);startSecondary()', self.main)

    def test_update_ui_uses_existing_guarded_updater_only(self):
        for call in ('updater.check()', 'updater.download()', 'updater.install()'):
            self.assertIn(call, self.update)

    def test_service_mode_does_not_duplicate_navigation_grid(self):
        self.assertIn('СЕРВІСНИЙ РЕЖИМ', self.main)
        self.assertNotIn('GridLayout{Layout.fillWidth:true;columns:4', self.main)

    def test_service_mode_hides_technical_provider_names_and_unknown_states(self):
        service = self.main.split('СЕРВІСНИЙ РЕЖИМ', 1)[1].split('Popup{id:flightMenu', 1)[0]
        for technical in ('telemetryRuntime.name', 'ext.source', 'net.transport'):
            self.assertNotIn(technical, service)
        for label in ('Поточний стан системи', 'Дані польоту:', 'Зовнішня навігація:', 'Мережеве з’єднання:'):
            self.assertIn(label, service)
        self.assertIn('states[value]||"потрібна перевірка"', self.main)

    def test_main_localizes_core_visible_surfaces(self):
        for text in (
            'ВІДЕО',
            'Основний',
            'Додатковий',
            'Поміняти місцями',
            'Дані польоту:',
            'Зовнішня навігація:',
            'Мережеве з’єднання:',
            'недоступно',
        ):
            self.assertIn(text, self.main)

    def test_navigation_stop_clears_media_sources(self):
        self.assertIn('player.source=""', self.main)
        self.assertIn('secondaryPlayer.source=""', self.main)

    def test_hover_help_delay_is_five_seconds(self):
        self.assertIn('property int delay:5000', self.hint)
        self.assertIn('showTimer.restart()', self.hint)

    def test_main_menu_is_a_single_translucent_drawer(self):
        self.assertIn('objectName: "mainMenuToggle"', self.home)
        self.assertIn('objectName: "mainMenuDrawer"', self.home)
        self.assertIn('color: "#f20a1420"', self.home)
        self.assertEqual(len(re.findall(r'action: "(devices|vehicles|station|service)"', self.home)), 4)
        self.assertEqual(self.home.count('objectName: "homePreflight"'), 1)

    def test_compact_home_keeps_delayed_help_on_primary_action(self):
        self.assertIn('HoverHint { text: "Рекомендована дія для поточного стану." }', self.home)


if __name__ == '__main__':
    unittest.main()
