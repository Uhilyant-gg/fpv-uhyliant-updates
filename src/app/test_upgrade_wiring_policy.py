import ast,unittest
from pathlib import Path
class Tests(unittest.TestCase):
 def test_main_constructs_guarded_session_and_binds_hardware_e2e_to_it(self):
  tree=ast.parse(Path(__file__).with_name('main.py').read_text(encoding='utf-8'));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
  session=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='FirmwareUpdateSession'];self.assertEqual(len(session),1);self.assertGreaterEqual(len(session[0].args),2);self.assertEqual(ast.unparse(session[0].args[0]),'fwexec');self.assertEqual(ast.unparse(session[0].args[1]),'d')
  e2e=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='HardwareE2ERuntime'];self.assertEqual(len(e2e),1);self.assertEqual([ast.unparse(x) for x in e2e[0].args[:5]],['d','diag','credentials','fw','fwsession'])
 def test_main_does_not_enable_destructive_transport_at_startup(self):
  text=Path(__file__).with_name('main.py').read_text(encoding='utf-8');self.assertNotIn('AuthenticatedCameraTransport(',text);self.assertNotIn('ExistingSshTransport(',text);self.assertNotIn('configure_transport(',text)
 def test_no_host_key_bypass_or_plaintext_secret_flags(self):
  root=Path(__file__).parent;text='\n'.join(p.read_text(encoding='utf-8') for p in [root/'openipc_ssh_transport.py',root/'authenticated_camera_transport.py']);self.assertNotIn('StrictHostKeyChecking=no',text);self.assertNotIn('sshpass',text);self.assertNotIn('--password',text)
if __name__=='__main__':unittest.main()
