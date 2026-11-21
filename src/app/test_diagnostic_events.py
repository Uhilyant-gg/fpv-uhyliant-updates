import unittest
from diagnostic_events import DiagnosticEvents
class Tests(unittest.TestCase):
 def test_records_structured_event(self):
  e=DiagnosticEvents(clock=lambda:42);self.assertTrue(e.record('video','warning','decoder stalled','cid',{'state':'unknown'}));self.assertEqual(e.snapshot()[0],{'timestamp':42,'correlationId':'cid','component':'video','level':'warning','message':'decoder stalled','detail':{'state':'unknown'}})
 def test_rejects_invalid_event(self):
  e=DiagnosticEvents();self.assertFalse(e.record('','error','x'));self.assertFalse(e.record('video','fatal','x'));self.assertFalse(e.record('video','error',''))
 def test_buffer_is_bounded(self):
  e=DiagnosticEvents(limit=2,clock=lambda:1);e.record('a','info','1');e.record('a','info','2');e.record('a','info','3');self.assertEqual([x['message'] for x in e.snapshot()],['2','3'])
if __name__=='__main__':unittest.main()
