import unittest
from unittest.mock import patch
from video import VideoRuntime
class FakeDevices:
 streams=[{'id':'main','device_id':'cam','name':'Main','kind':'main','protocol':'rtsp','port':554,'path':'/stream=0','video_profile_id':'main-profile','enabled':True},{'id':'sub','device_id':'cam','name':'Sub','kind':'sub','protocol':'rtsp','port':554,'path':'/stream=1','video_profile_id':'sub-profile','enabled':True}]
 items=[{'id':'cam','host':'192.168.1.10'}]
 videoProfiles=[{'id':'main-profile','codec':'h265','width':1920,'height':1080,'fps':60,'latency_mode':'low_latency'},{'id':'sub-profile','codec':'h264','width':640,'height':360,'fps':30,'latency_mode':'balanced'}]
class VideoRuntimeTests(unittest.TestCase):
 @patch('video.socket.create_connection')
 def test_diagnostics_follow_selected_stream_and_profile_metadata(self,connection):
  connection.return_value.__enter__.return_value=object();r=VideoRuntime(FakeDevices());self.assertTrue(r.prepare('main'));self.assertEqual(r.diagnostics['kind'],'main');self.assertEqual(r.diagnostics['codec'],'h265');self.assertEqual(r.diagnostics['width'],1920);self.assertEqual(r.diagnostics['fps'],60);self.assertIsNotNone(r.diagnostics['endpointCheckMs']);self.assertTrue(r.prepare('sub'));self.assertEqual(r.diagnostics['kind'],'sub');self.assertEqual(r.diagnostics['codec'],'h264')
 def test_missing_stream_is_unavailable_not_invented(self):
  r=VideoRuntime(FakeDevices());self.assertFalse(r.prepare('missing'));self.assertIsNone(r.diagnostics['streamId']);self.assertIsNone(r.diagnostics['codec']);self.assertIsNone(r.diagnostics['endpointCheckMs'])
if __name__=='__main__':unittest.main()
