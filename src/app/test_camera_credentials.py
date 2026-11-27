import unittest
from camera_credentials import CameraCredentials
class Tests(unittest.TestCase):
 def test_session_secret_snapshot_and_clear(self):
  c=CameraCredentials();c.username='admin';c.password='top-secret';self.assertEqual(c.snapshot(),{'username':'admin','hasPassword':True});self.assertNotIn('top-secret',repr(c.snapshot()));c.clear();self.assertEqual(c.password,'')
 def test_reset_clears_password(self):
  c=CameraCredentials();c.password='secret';c.reset();self.assertEqual(c.password,'');self.assertEqual(c.username,'root')
if __name__=='__main__':unittest.main()
