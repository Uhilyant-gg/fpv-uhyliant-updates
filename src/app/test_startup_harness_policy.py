import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
 def test_main_has_durable_startup_boundaries(self):
  text=(ROOT/'src/app/main.py').read_text(encoding='utf-8')
  for value in ('--startup-diagnostics','main-entry','qt-imports-begin','qgui-application-begin','application-objects-begin','qml-load-begin','event-loop-begin','startup-ready'):self.assertIn(value,text)
 def test_release_runs_packaged_diagnostic_probe(self):
  text=(ROOT/'.github/workflows/automated-ota.yml').read_text(encoding='utf-8')
  self.assertIn('--startup-diagnostics',text);self.assertIn('--noupx',text)
if __name__=='__main__':unittest.main()
