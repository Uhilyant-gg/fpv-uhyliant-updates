import unittest
from pathlib import Path
class Tests(unittest.TestCase):
 def test_credentials_fields_are_masked_and_cleared(self):
  q=Path(__file__).with_name('FirmwareCenter.qml').read_text(encoding='utf-8');self.assertIn('placeholderText:"Логін камери"',q);self.assertIn('placeholderText:"Пароль камери"',q);self.assertIn('echoMode:TextInput.Password',q);self.assertIn('ImhSensitiveData',q);self.assertIn('cameraCredentials.clear()',q);self.assertIn('onClicked:root.closePanel()',q)
if __name__=='__main__':unittest.main()
