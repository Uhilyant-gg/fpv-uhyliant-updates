import unittest
from pathlib import Path


class Tests(unittest.TestCase):
    def setUp(self):
        self.qml = Path(__file__).with_name('FirmwareCenter.qml').read_text(encoding='utf-8')

    def test_password_field_is_masked_and_marks_sensitive_input(self):
        self.assertRegex(
            self.qml,
            r'TextField\s*\{[^{}]*id:passwordField[^{}]*echoMode:TextInput\.Password[^{}]*inputMethodHints:[^{}]*Qt\.ImhSensitiveData',
        )

    def test_credentials_are_session_only_and_cleared_by_close_path(self):
        self.assertIn('function clearSensitive()', self.qml)
        self.assertIn('passwordField.text=""', self.qml)
        self.assertIn('cameraCredentials.clear()', self.qml)
        self.assertIn('function closePanel(){clearSensitive();', self.qml)
        self.assertRegex(self.qml, r'onClicked:\s*root\.closePanel\(\)')

    def test_password_is_not_persisted_by_firmware_ui(self):
        for forbidden in ('settings.password', 'savePassword', 'persistPassword', 'passwordFile'):
            self.assertNotIn(forbidden, self.qml)


if __name__ == '__main__':
    unittest.main()
