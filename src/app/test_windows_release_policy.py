import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
class WindowsReleasePolicyTests(unittest.TestCase):
 def test_release_uses_python_311_and_pinned_qt(self):
  workflow=(ROOT/'.github/workflows/automated-ota.yml').read_text(encoding='utf-8')
  requirements=(ROOT/'src/requirements.txt').read_text(encoding='utf-8')
  self.assertIn("python-version: '3.11'",workflow)
  self.assertNotIn("python-version: '3.12'",workflow)
  self.assertIn('PySide6==6.8.3',requirements)
 def test_fpv_players_do_not_attach_audio_output(self):
  qml=(ROOT/'src/app/Main.qml').read_text(encoding='utf-8')
  self.assertNotIn('AudioOutput{',qml)
  self.assertNotIn('audioOutput:',qml)
  self.assertNotIn('PLACEHOLDER',qml)
if __name__=='__main__':unittest.main()
