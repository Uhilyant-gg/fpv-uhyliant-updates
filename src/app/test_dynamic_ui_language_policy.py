from source_text import read_source
from pathlib import Path
import unittest


class DynamicUiLanguagePolicyTests(unittest.TestCase):
    def setUp(self):
        here = Path(__file__).parent
        names = (
            'video.py',
            'msp_runtime.py',
            'firmware_center.py',
            'firmware_executor.py',
            'camera_presets.py',
            'camera_preset_executor.py',
            'post_flash_verify.py',
            'updater_engine.py',
            'pairing.py',
        )
        self.sources = {name: read_source(here / name) for name in names}

    def test_video_user_errors_are_ukrainian(self):
        source = self.sources['video.py']
        for obsolete in ('Video profile', 'runtime підтримує', 'endpoint metadata', 'metadata змінилися'):
            self.assertNotIn(obsolete, source)
        for expected in ('Відеопрофіль', 'модуль відтворення', 'Метадані кінцевої точки RTSP', 'метадані змінилися'):
            self.assertIn(expected, source)

    def test_msp_dynamic_error_is_ukrainian(self):
        self.assertIn('MSP: відповідь із помилкою для команди', self.sources['msp_runtime.py'])
        self.assertNotIn('MSP error response for command', self.sources['msp_runtime.py'])

    def test_firmware_dynamic_copy_is_ukrainian_without_changing_enum_values(self):
        source = self.sources['firmware_center.py']
        for obsolete in (
            'Primary installation',
            '"title":"Upgrade"',
            '"title":"Unknown"',
            'Firmware image не',
            'Execution plan не',
            'Destructive flashing',
            'Plan prepared; hardware executor not attached',
        ):
            self.assertNotIn(obsolete, source)
        for enum_value in ('"primary"', '"upgrade"', '"recovery-fullflash"'):
            self.assertIn(enum_value, source)

    def test_executor_user_messages_are_ukrainian_without_changing_states(self):
        firmware = self.sources['firmware_executor.py']
        preset = self.sources['camera_preset_executor.py']
        for obsolete in (
            'firmware operation',
            'Execution plan',
            'immutable approval',
            'Approved device',
            'Verified OpenIPC identity',
            'Hardware identity',
            'Post-operation verification failed',
            'preset operation',
            'Camera preset plan',
            'verified hardware identity',
            'Post-preset verified hardware observation unavailable',
        ):
            self.assertNotIn(obsolete, firmware + '\n' + preset)
        for state in (
            "'blocked'",
            "'hardware-validation-pending'",
            "'executing'",
            "'reboot-pending'",
            "'verified'",
            "'applied-pending-verification'",
        ):
            self.assertIn(state, firmware + '\n' + preset)

    def test_post_flash_details_are_ukrainian(self):
        source = self.sources['post_flash_verify.py']
        for obsolete in (
            'Device rediscovered',
            'Device not rediscovered',
            'OpenIPC evidence',
            'Platform/sensor',
            'Observed firmware',
            'Hardware identity',
        ):
            self.assertNotIn(obsolete, source)
        self.assertIn('Пристрій повторно виявлено', source)
        self.assertIn('Спостережувана прошивка', source)

    def test_camera_preset_dynamic_copy_is_ukrainian(self):
        source = self.sources['camera_presets.py']
        for obsolete in (
            'Preset не',
            'verified device identity',
            'hardware identity unavailable',
            'Camera preset apply plan',
        ):
            self.assertNotIn(obsolete, source)
        self.assertIn('апаратний виконавець не підключений', source)

    def test_updater_status_copy_is_ukrainian(self):
        source = self.sources['updater_engine.py']
        for obsolete in ("'Manifest ", " manifest'", "ready state", " MB'"):
            self.assertNotIn(obsolete, source)
        self.assertIn('маніфест', source)
        self.assertIn(' МБ', source)

    def test_pairing_errors_are_ukrainian_without_changing_trust_state_contract(self):
        source = self.sources['pairing.py']
        for obsolete in (
            'OS-protected secret store unavailable',
            'pairing metadata store unavailable',
            'invalid pairing metadata',
            'invalid trust record',
            'duplicate trust record',
            'confirm rollback failed',
            'trusted metadata references a missing protected secret',
            'revoke rollback failed',
            'reconciliation requires both protected secret and metadata stores',
            'reconciliation incomplete',
        ):
            self.assertNotIn(obsolete, source)
        for contract in ("'state':'pending'", "'state':'trusted'", "'secretRef'", "'pairing/'"):
            self.assertIn(contract, source)
        self.assertIn('узгодження не завершено', source)


if __name__ == '__main__':
    unittest.main()
