import tempfile,unittest
from pathlib import Path
from diagnostic_events import DiagnosticEvents
from diagnostics_runtime import DiagnosticsRuntime
class Obj:pass
class Tests(unittest.TestCase):
 def base(self):
  d=Obj();d._items=[];links=Obj();links.snapshot={'network':{'state':'unavailable'}};links.changed=Obj();links.changed.emit=lambda:None;t=Obj();t.name='MSP';t.available=False;t.error='';t.telemetry={};u=Obj();u.updateState='idle';u.updateStatus='Готово';u.availableVersion='';u.progress=0;return d,links,t,u
 def test_runtime_collects_real_boundaries_without_inventing_values(self):
  d,links,t,u=self.base();d._items=[{'id':'1','firmware':None,'password':'secret'}];links.snapshot={'network':{'state':'ready'}};t.name='MAVLink';t.telemetry={'connected':None}
  with tempfile.TemporaryDirectory() as root:
   r=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root);b=r.build();self.assertIsNone(b['devices'][0]['firmware']);self.assertEqual(b['devices'][0]['password'],'[redacted]');self.assertIsNone(b['protocols']['telemetry']['connected'])
 def test_export_creates_bundle(self):
  d,links,t,u=self.base()
  with tempfile.TemporaryDirectory() as root:
   r=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root);p=Path(r.export());self.assertTrue(p.is_file());self.assertEqual(p.parent.name,'diagnostics')
 def test_only_allowlisted_non_mutating_action_executes(self):
  d,links,t,u=self.base()
  with tempfile.TemporaryDirectory() as root:
   r=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root);self.assertTrue(r.applyRemediation('refresh-network'));self.assertFalse(r.applyRemediation('shell'));self.assertFalse(r.applyRemediation('set-static-ip'));self.assertEqual(r.build()['lastRemediation']['action'],'refresh-network')
 def test_rediscover_requires_actual_device_boundary(self):
  d,links,t,u=self.base();calls=[];d.discoverOpenIPC=lambda:calls.append(True)
  with tempfile.TemporaryDirectory() as root:
   r=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root);self.assertTrue(r.applyRemediation('rediscover'));self.assertEqual(calls,[True])
if __name__=='__main__':unittest.main()
