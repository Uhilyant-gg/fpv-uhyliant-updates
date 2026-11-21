from pathlib import Path
import unittest


class DynamicUiLanguagePolicyTests(unittest.TestCase):
    def setUp(self):
        here=Path(__file__).parent
        self.sources={name:(here/name).read_text(encoding='utf-8') for name in ('video.py','msp_runtime.py','firmware_center.py','camera_presets.py','updater_engine.py')}

    def test_video_user_errors_are_ukrainian(self):
        source=self.sources['video.py']
        for obsolete in ('Video profile','runtime підтримує','endpoint metadata','metadata змінилися'):self.assertNotIn(obsolete,source)
        for expected in ('Відеопрофіль','модуль відтворення','Метадані кінцевої точки RTSP','метадані змінилися'):self.assertIn(expected,source)

    def test_msp_dynamic_error_is_ukrainian(self):
        self.assertIn('MSP: відповідь із помилкою для команди',self.sources['msp_runtime.py'])
        self.assertNotIn('MSP error response for command',self.sources['msp_runtime.py'])

    def test_firmware_dynamic_copy_is_ukrainian_without_changing_enum_values(self):
        source=self.sources['firmware_center.py']
        for obsolete in ('Primary installation','"title":"Upgrade"','"title":"Unknown"','Firmware image не','Execution plan не','Destructive flashing','Plan prepared; hardware executor not attached'):self.assertNotIn(obsolete,source)
        for enum_value in ('"primary"','"upgrade"','"recovery-fullflash"'):self.assertIn(enum_value,source)

    def test_camera_preset_dynamic_copy_is_ukrainian(self):
        source=self.sources['camera_presets.py']
        for obsolete in ('Preset не','verified device identity','hardware identity unavailable','Camera preset apply plan'):self.assertNotIn(obsolete,source)
        self.assertIn('апаратний виконавець не підключений',source)

    def test_updater_status_copy_is_ukrainian(self):
        source=self.sources['updater_engine.py']
        for obsolete in ("'Manifest "," manifest'","ready state"," MB'"):self.assertNotIn(obsolete,source)
        self.assertIn('маніфест',source)
        self.assertIn(' МБ',source)


if __name__=='__main__':unittest.main()
