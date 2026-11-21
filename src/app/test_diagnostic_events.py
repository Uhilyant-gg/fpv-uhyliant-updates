import unittest
from diagnostic_events import DiagnosticEvents
class Tests(unittest.TestCase):
 def test_records_structured_event(self):
  e=DiagnosticEvents(clock=lambda:42);self.assertTrue(e.record('video','warning','decoder stalled','cid',{'state':'unknown'}));self.assertEqual(e.snapshot()[0],{'timestamp':42,'correlationId':'cid','component':'video','level':'warning','message':'decoder stalled','detail':{'state':'unknown'}})
 def test_rejects_invalid_event(self):
  e=DiagnosticEvents();self.assertFalse(e.record('','error','x'));self.assertFalse(e.record('video','fatal','x'));self.assertFalse(e.record('video','error',''))
 def test_buffer_is_bounded(self):
  e=DiagnosticEvents(limit=2,clock=lambda:1);e.record('a','info','1');e.record('a','info','2');e.record('a','info','3');self.assertEqual([x['message'] for x in e.snapshot()],['2','3'])
 def test_snapshot_and_record_do_not_leak_mutable_detail(self):
  e=DiagnosticEvents(clock=lambda:1);detail={'nested':{'state':'ready'}};e.record('firmware','info','x','cid',detail);detail['nested']['state']='mutated';snapshot=e.snapshot();snapshot[0]['detail']['nested']['state']='also-mutated';self.assertEqual(e.snapshot()[0]['detail']['nested']['state'],'ready')
 def test_correlated_filters_lifecycle_without_exposing_internal_buffer(self):
  e=DiagnosticEvents(clock=lambda:1);e.record('firmware','info','start','cid',{'step':'dispatch'});e.record('video','warning','stall','cid');e.record('firmware','error','fail','other');items=e.correlated('cid','firmware');self.assertEqual([x['message'] for x in items],['start']);items[0]['message']='mutated';self.assertEqual(e.correlated('cid','firmware')[0]['message'],'start');self.assertEqual(e.correlated(''),'[]' if False else [])
if __name__=='__main__':unittest.main()
