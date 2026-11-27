import unittest
from authenticated_camera_transport import AuthenticatedCameraTransport
class Creds:
 username='root'
 def secret(self):return 'super-secret'
class Channel:
 def recv_exit_status(self):return 0
class Stream:
 channel=Channel()
class Client:
 def __init__(self,fail=False):self.calls=[];self.commands=[];self.fail=fail
 def connect(self,*a,**kw):self.calls.append((a,kw));
 def close(self):pass
 def exec_command(self,cmd,timeout=None):self.commands.append(cmd);return None,Stream(),None
class Tests(unittest.TestCase):
 def test_password_never_enters_command_and_fixed_upgrade_only(self):
  c=Client();t=AuthenticatedCameraTransport(Creds(),lambda:c);self.assertTrue(t.authenticate('192.168.1.50'));self.assertTrue(t.run('192.168.1.50',['sysupgrade','-k','-r']));self.assertEqual(c.commands,['sysupgrade -k -r']);self.assertNotIn('super-secret',repr(c.commands));self.assertFalse(t.run('192.168.1.50',['reboot']))
 def test_invalid_host_is_fail_closed(self):self.assertFalse(AuthenticatedCameraTransport(Creds(),Client).authenticate('192.168.1.50;reboot'))
if __name__=='__main__':unittest.main()
