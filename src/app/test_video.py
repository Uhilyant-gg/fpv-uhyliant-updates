import unittest
from unittest.mock import patch
from video import VideoRuntime

class FakeDevices:
    streams=[{'id':'main','device_id':'cam','name':'Main','kind':'main','protocol':'rtsp','port':554,'path':'/stream=0','enabled':True},{'id':'sub','device_id':'cam','name':'Sub','kind':'sub','protocol':'rtsp','port':554,'path':'/stream=1','enabled':True}]
    items=[{'id':'cam','host':'192.168.1.10'}]

class VideoRuntimeTests(unittest.TestCase):
    @patch('video.socket.create_connection')
    def test_diagnostics_follow_selected_stream(self,connection):
        connection.return_value.__enter__.return_value=object();runtime=VideoRuntime(FakeDevices())
        self.assertTrue(runtime.prepare('main'));self.assertEqual(runtime.diagnostics['kind'],'main');self.assertEqual(runtime.diagnostics['path'],'/stream=0')
        self.assertTrue(runtime.prepare('sub'));self.assertEqual(runtime.diagnostics['kind'],'sub');self.assertEqual(runtime.diagnostics['streamName'],'Sub');self.assertEqual(runtime.diagnostics['path'],'/stream=1')
    def test_missing_stream_is_unavailable_not_invented(self):
        runtime=VideoRuntime(FakeDevices());self.assertFalse(runtime.prepare('missing'));self.assertIsNone(runtime.diagnostics['streamId']);self.assertIsNone(runtime.diagnostics['kind'])

if __name__=='__main__':unittest.main()
