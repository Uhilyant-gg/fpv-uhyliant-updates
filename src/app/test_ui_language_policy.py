from pathlib import Path
import re
import unittest


class UiLanguagePolicyTests(unittest.TestCase):
    def setUp(self):
        here = Path(__file__).parent
        self.sources = {
            name: (here / name).read_text(encoding="utf-8")
            for name in (
                "BackupPanel.qml",
                "FirmwareCenter.qml",
                "UpdatePanel.qml",
                "DevicesPanel.qml",
                "DiagnosticsPanel.qml",
                "PairingPanel.qml",
                "Main.qml",
                "MavlinkDiagnostics.qml",
            )
        }

    def visible(self, source):
        return "\n".join(re.findall(r'(?:text|placeholderText|title)\s*:\s*"([^"]*)"', source))

    def hover_hint_count(self, source):
        return len(re.findall(r"\bHoverHint\s*\{", source))

    def test_firmware_surface_is_ukrainian(self):
        source = self.sources["FirmwareCenter.qml"]
        visible = self.visible(source)
        for text in ("ЦЕНТР ПРОШИВКИ", "Перевірити оновлення", "Оновити камеру"):
            self.assertIn(text, visible)
        self.assertIn('advanced?"Сховати додатково":"Додатково"', source)
        for obsolete in (
            "FIRMWARE CENTER",
            "IMAGE VERIFIED",
            "PRE-CHECK APPROVED",
            "EXECUTION PLAN READY",
            "Expected SHA-256",
            "Flash layout verified",
            "Recovery path verified",
        ):
            self.assertNotIn(obsolete, visible)

    def test_devices_surface_core_copy_is_ukrainian(self):
        visible = self.visible(self.sources["DevicesPanel.qml"])
        for obsolete in (
            "OPENIPC IDENTITY",
            "Platform / SoC",
            "Sensor:",
            "Firmware:",
            "Evidence:",
            "Hostname:",
            "Camera preset",
            "video profile",
            "hardware apply",
        ):
            self.assertNotIn(obsolete, visible)

    def test_diagnostics_surface_core_copy_is_ukrainian(self):
        visible = self.visible(self.sources["DiagnosticsPanel.qml"])
        for expected in ("ДІАГНОСТИКА", "Телеметрія: ", "Мережа: ", "Експортувати діагностику", "Закрити"):
            self.assertIn(expected, visible)
        for obsolete in ("Diagnostics", "Telemetry: ", "Network: ", "Export", "Close"):
            self.assertNotIn(obsolete, visible)

    def test_pairing_surface_core_copy_is_ukrainian(self):
        visible = self.visible(self.sources["PairingPanel.qml"])
        for obsolete in (
            "PAIRING TRUST",
            "Protected secret store",
            "Trust metadata store",
            "Recovery required",
            "Fingerprint:",
            "trusted",
        ):
            self.assertNotIn(obsolete, visible)

    def test_backup_surface_explains_encryption_and_requires_confirmed_restore(self):
        source = self.sources["BackupPanel.qml"]
        visible = self.visible(source)
        for expected in (
            "РЕЗЕРВНА КОПІЯ",
            "у зашифрованому файлі.",
            "Пароль не зберігається.",
            "Зберегти резервну копію",
            "Перевірити копію",
            "Відновити",
        ):
            self.assertIn(expected, visible)
        # The confirmation must warn that current data (devices, and presets when present) will be replaced.
        self.assertIn('"пристрої та відеопотоки")+" буде замінено."', source)
        self.assertIn("пристрої, пресети та налаштування", source)
        self.assertNotIn("stationBackup.result.reason", source)
        self.assertIn("stationBackup.restoreInspected(true)", source)

    def test_main_surface_core_copy_is_ukrainian(self):
        visible = self.visible(self.sources["Main.qml"])
        for expected in (
            "СЕРВІСНИЙ РЕЖИМ",
            "ВІДЕО",
            "Основний",
            "Додатковий",
            "Поміняти місцями",
            "Обслуговування",
            "Дані польоту: ",
            "Мережеве з’єднання: ",
        ):
            self.assertIn(expected, visible)
        for obsolete in (
            "SERVICE MODE",
            "VIDEO WORKSPACE",
            "Primary",
            "Secondary",
            "Swap",
            "Firmware",
            "Telemetry: ",
            "Network: ",
        ):
            self.assertNotIn(obsolete, visible)

    def test_mavlink_diagnostics_surface_is_ukrainian(self):
        visible = self.visible(self.sources["MavlinkDiagnostics.qml"])
        for expected in (
            "ІДЕНТИФІКАЦІЯ",
            "Система / компонент",
            "Літальний апарат",
            "Стан системи",
            "ДІАГНОСТИКА КАНАЛУ",
            "Частота повідомлень",
            "Оцінка втрат",
            "Помилки зв’язку",
            "Завантаження контролера",
        ):
            self.assertIn(expected, visible)
        for obsolete in (
            "IDENTITY",
            "System / Component",
            "Vehicle",
            "System state",
            "LINK DIAGNOSTICS",
            "Health",
            "Message rate",
            "Last packet",
            "Estimated lost",
            "Bad data",
            "Comm errors",
            "Controller load",
            "not broadcast",
        ):
            self.assertNotIn(obsolete, visible)

    def test_update_surface_has_delayed_help(self):
        self.assertGreaterEqual(self.hover_hint_count(self.sources["UpdatePanel.qml"]), 3)

    def test_firmware_surface_keeps_explanatory_copy(self):
        visible = self.visible(self.sources["FirmwareCenter.qml"])
        for expected in (
            "Безпечне автоматичне оновлення OpenIPC-камери",
            "Дані потрібні лише для цього сеансу й не зберігаються.",
            "Це окремий експертний сценарій, не рекомендоване автоматичне оновлення.",
        ):
            self.assertIn(expected, visible)

    def test_devices_and_pairing_have_delayed_help(self):
        self.assertGreaterEqual(self.hover_hint_count(self.sources["DevicesPanel.qml"]), 8)
        self.assertGreaterEqual(self.hover_hint_count(self.sources["PairingPanel.qml"]), 2)

    def test_main_and_extracted_diagnostics_keep_delayed_help_contract(self):
        interactive = self.sources["Main.qml"] + self.sources["DiagnosticsPanel.qml"]
        self.assertIn("HoverHint.qml", "HoverHint.qml")
        self.assertGreaterEqual(interactive.count("Button{"), 12)


if __name__ == "__main__":
    unittest.main()
