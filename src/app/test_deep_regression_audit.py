import unittest
from pathlib import Path
class Tests(unittest.TestCase):
 def setUp(self):self.root=Path(__file__).parent
 def test_no_scrubbed_runtime_placeholders_in_active_runtime_path(self):
  bad=[]
  for name in ('devices_routeaware.py','route_discovery.py','main.py','updater_engine.py','firmware_update_session.py'):
   p=self.root/name
   if '<scrubbed-url-domain>' in p.read_text(encoding='utf-8',errors='ignore'):bad.append(name)
  self.assertEqual(bad,[])
 def test_openipc_discovery_has_both_fixed_real_paths(self):
  text=(self.root/'route_discovery.py').read_text(encoding='utf-8');self.assertIn('/api/v1/config.json',text);self.assertIn('/cgi-bin/status.cgi',text)
 def test_updater_requires_launcher_helper_and_current_payload(self):
  text=(self.root/'updater_engine.py').read_text(encoding='utf-8');self.assertIn("FPV-Uhyliant-Update.exe",text);self.assertIn("FPV-Uhyliant-Launcher.exe",text);self.assertIn("app'/'current'/'FPV-Uhyliant.exe",text)
 def test_release_pipeline_packages_paramiko(self):
  workflow=(self.root.parent.parent/'.github'/'workflows'/'automated-ota.yml').read_text(encoding='utf-8');self.assertIn('--collect-all paramiko',workflow)
if __name__=='__main__':unittest.main()
