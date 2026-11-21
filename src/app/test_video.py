import unittest
from unittest.mock import patch
from PySide6.QtCore import QObject,Signal
from video import VideoRuntime,VideoWorkspaceRuntime
class FakeDevices(QObject):
 streamsChanged=Signal();changed=Signal();profilesChanged=Signal()
 def __init__(self):
  super().__init__();self._active='cam';self.streams=[{'id':'main','device_id':'cam','name':'Main','kind':'main','protocol':'rtsp','port':554,'path':'/stream=0','video_profile_id':'main-profile','enabled':True},{'id':'sub','device_id':'cam','name':'Sub','kind':'sub','protocol':'rtsp','port':554,'path':'/stream=1','video_profile_id':'sub-profile','enabled':True}];self.items=[{'id':'cam','host':'192.168.1.10'},{'id':'other','host':'192.168.1.20'}];self.videoProfiles=[{'id':'main-profile','codec':'h265','width':1920,'height':1080,'fps':60,'latency_mode':'low_latency'},{'id':'sub-profile','codec':'h264','width':640,'height':360,'fps':30,'latency_mode':'balanced'}]
 @property
 def activeStreams(self):return [s for s in self.streams if s.get('device_id')==self._active]
class VideoRuntimeTests(unittest.TestCase):
 @patch('video.socket.create_connection')
 def test_diagnostics_follow_selected_stream_and_profile_metadata(self,c):
  c.return_value.__enter__.return_value=object();r=VideoRuntime(FakeDevices());self.assertTrue(r.prepare('main'));self.assertEqual(r.diagnostics['codec'],'h265');self.assertTrue(r.prepare('sub'));self.assertEqual(r.diagnostics['codec'],'h264')
 @patch('video.socket.create_connection')
 def test_path_is_canonicalized_without_invalidating_same_source(self,c):
  c.return_value.__enter__.return_value=object();d=FakeDevices();d.streams[0]['path']='stream=0';r=VideoRuntime(d);self.assertTrue(r.prepare('main'));self.assertEqual(r.url,'rtsp://192.168.1.10:554/stream=0');r.markPlaying();self.assertEqual(r.state,'playing');self.assertTrue(r.reconnect());self.assertEqual(r.state,'ready')
 def test_missing_stream_is_unavailable_not_invented(self):
  r=VideoRuntime(FakeDevices());self.assertFalse(r.prepare('missing'));self.assertIsNone(r.diagnostics['streamId']);self.assertIsNone(r.diagnostics['codec']);self.assertIsNone(r.diagnostics['endpointCheckMs'])
 def test_invalid_endpoint_metadata_does_not_attempt_connection(self):
  d=FakeDevices();d.streams[0]['port']='bad';r=VideoRuntime(d)
  with patch('video.socket.create_connection') as c:self.assertFalse(r.prepare('main'));c.assert_not_called();self.assertIsNone(r.diagnostics['streamId']);self.assertIsNone(r.diagnostics['endpointCheckMs'])
 @patch('video.socket.create_connection')
 def test_primary_secondary_runtime_state_is_isolated(self,c):
  c.return_value.__enter__.return_value=object();w=VideoWorkspaceRuntime(FakeDevices());w.setPipEnabled(True);self.assertTrue(w.preparePrimary('main'));self.assertTrue(w.prepareSecondary('sub'));w.primary.playbackError('primary only');self.assertEqual(w.primary.state,'error');self.assertEqual(w.secondary.state,'ready')
 @patch('video.socket.create_connection')
 def test_same_stream_cannot_back_both_decoders(self,c):
  c.return_value.__enter__.return_value=object();w=VideoWorkspaceRuntime(FakeDevices());w.setPipEnabled(True);self.assertTrue(w.preparePrimary('main'));self.assertFalse(w.prepareSecondary('main'));self.assertEqual(w.secondary.streamId,'')
 @patch('video.socket.create_connection')
 def test_primary_takeover_stops_secondary_same_stream(self,c):
  c.return_value.__enter__.return_value=object();w=VideoWorkspaceRuntime(FakeDevices());w.setPipEnabled(True);self.assertTrue(w.prepareSecondary('sub'));self.assertTrue(w.preparePrimary('sub'));self.assertEqual(w.secondary.state,'stopped');self.assertEqual(w.secondary.streamId,'');self.assertEqual(w.primary.streamId,'sub')
 @patch('video.socket.create_connection')
 def test_pip_off_stops_secondary_only(self,c):
  c.return_value.__enter__.return_value=object();w=VideoWorkspaceRuntime(FakeDevices());w.setPipEnabled(True);w.preparePrimary('main');w.prepareSecondary('sub');w.setPipEnabled(False);self.assertEqual(w.secondary.state,'stopped');self.assertEqual(w.primary.streamId,'main')
 def test_secondary_cannot_prepare_while_pip_off(self):
  w=VideoWorkspaceRuntime(FakeDevices());self.assertFalse(w.prepareSecondary('sub'));self.assertEqual(w.secondary.state,'stopped')
 @patch('video.socket.create_connection',side_effect=OSError('offline'))
 def test_failed_secondary_prepare_disables_pip(self,c):
  w=VideoWorkspaceRuntime(FakeDevices());w.setPipEnabled(True);self.assertFalse(w.prepareSecondary('sub'));self.assertFalse(w.pipEnabled);self.assertEqual(w.secondary.state,'error')
 @patch('video.socket.create_connection')
 def test_reconnect_fails_closed_if_stream_was_removed(self,c):
  c.return_value.__enter__.return_value=object();d=FakeDevices();r=VideoRuntime(d);self.assertTrue(r.prepare('main'));d.streams=[];self.assertFalse(r.reconnect());self.assertEqual(r.state,'error');self.assertEqual(r.streamId,'');self.assertIsNone(r.diagnostics['endpointCheckMs'])
 @patch('video.socket.create_connection')
 def test_active_device_change_invalidates_prepared_runtime(self,c):
  c.return_value.__enter__.return_value=object();d=FakeDevices();w=VideoWorkspaceRuntime(d);self.assertTrue(w.preparePrimary('main'));d._active='other';d.streamsChanged.emit();self.assertEqual(w.primary.streamId,'');self.assertEqual(w.primary.state,'error');self.assertIsNone(w.primary.diagnostics['codec'])
 @patch('video.socket.create_connection')
 def test_stream_metadata_change_invalidates_and_clears_old_metadata(self,c):
  c.return_value.__enter__.return_value=object();d=FakeDevices();w=VideoWorkspaceRuntime(d);self.assertTrue(w.preparePrimary('main'));d.streams[0]['path']='/new';d.streamsChanged.emit();self.assertEqual(w.primary.streamId,'');self.assertIsNone(w.primary.diagnostics['path']);self.assertIsNone(w.primary.diagnostics['codec'])
 @patch('video.socket.create_connection')
 def test_profile_change_invalidates_prepared_runtime(self,c):
  c.return_value.__enter__.return_value=object();d=FakeDevices();w=VideoWorkspaceRuntime(d);self.assertTrue(w.preparePrimary('main'));d.videoProfiles[0]['fps']=30;d.profilesChanged.emit();self.assertEqual(w.primary.streamId,'');self.assertIsNone(w.primary.diagnostics['fps'])
 @patch('video.socket.create_connection')
 def test_secondary_invalidation_disables_pip(self,c):
  c.return_value.__enter__.return_value=object();d=FakeDevices();w=VideoWorkspaceRuntime(d);w.setPipEnabled(True);self.assertTrue(w.preparePrimary('main'));self.assertTrue(w.prepareSecondary('sub'));d.streams[1]['enabled']=False;d.streamsChanged.emit();self.assertFalse(w.pipEnabled);self.assertEqual(w.secondary.streamId,'');self.assertEqual(w.primary.streamId,'main')
 @patch('video.socket.create_connection')
 def test_reconnect_rejects_changed_endpoint_until_reprepared(self,c):
  c.return_value.__enter__.return_value=object();d=FakeDevices();r=VideoRuntime(d);self.assertTrue(r.prepare('main'));d.items[0]['host']='192.168.1.11';self.assertFalse(r.reconnect());self.assertEqual(r.streamId,'');self.assertIsNone(r.diagnostics['host'])
 def test_playback_events_do_not_resurrect_stopped_runtime(self):
  r=VideoRuntime(FakeDevices());r.stop();r.markPlaying();r.playbackError('late');r.markStalled('late');self.assertEqual(r.state,'stopped');self.assertEqual(r.streamId,'')
if __name__=='__main__':unittest.main()
