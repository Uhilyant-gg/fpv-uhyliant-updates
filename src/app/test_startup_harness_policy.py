import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
 def test_main_has_durable_startup_boundaries(self):
  text=(ROOT/'src/app/main.py').read_text(encoding='utf-8')
  for value in ('--startup-diagnostics','--acceptance-report','main-entry','window-visible','qt-imports-begin','qgui-application-begin','application-objects-begin','qml-load-begin','event-loop-begin','startup-ready','harness.mark(\'health\''):self.assertIn(value,text)
 def test_packaged_diagnostic_workflow_is_clean_debug_onedir(self):
  text=(ROOT/'.github/workflows/startup-diagnostics.yml').read_text(encoding='utf-8')
  for value in ('python -m venv','.venv','pyinstaller==6.11.1','--onedir','--debug bootloader','--noupx','--startup-diagnostics'):self.assertIn(value,text)
if __name__=='__main__':unittest.main()
