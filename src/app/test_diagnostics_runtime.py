import tempfile,unittest
from pathlib import Path
from diagnostic_events import DiagnosticEvents
from diagnostics_runtime import DiagnosticsRuntime
class Obj:pass
class Tests(unittest.TestCase):
 def test_runtime_collects_real_boundaries_without_inventing_values(self):
  d=Obj();d._items=[{'id':'1','firmware':None,'password':'secret'}];links=Obj();links.snapshot={'network':{'state':'ready'}};t=Obj();t.name='MAVLink';t.available=False;t.error='';t.telemetry={'connected':None};u=Obj();u.updateState='idle';u.updateStatus='Готово';u.availableVersion='';u.progress=0
  with tempfile.TemporaryDirectory() as root:
   r=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root);b=r.build();self.assertIsNone(b['devices'][0]['firmware']);self.assertEqual(b['devices'][0]['password'],'[redacted]');self.assertIsNone(b['protocols']['telemetry']['connected'])
 def test_export_creates_bundle(self):
  d=Obj();d._items=[];links=Obj();links.snapshot={};t=Obj();t.name='MSP';t.available=False;t.error='';t.telemetry={};u=Obj();u.updateState='idle';u.updateStatus='Готово';u.availableVersion='';u.progress=0
  with tempfile.TemporaryDirectory() as root:
   r=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root);p=Path(r.export());self.assertTrue(p.is_file());self.assertEqual(p.parent.name,'diagnostics')
if __name__=='__main__':unittest.main()
