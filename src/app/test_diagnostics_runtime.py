import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
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
 def test_manual_probe_contributes_fresh_device_evidence(self):
  d,links,t,u=self.base();d._items=[{'id':'1','host':'192.168.1.50','openipcIdentity':{'verified':True}}];d._discovered=[];d._manual_result={'host':'192.168.1.50','reachable':True,'openipc':True,'identity':{'verified':True}}
  with tempfile.TemporaryDirectory() as root, patch('diagnostics_runtime.interfaces',return_value=[]), patch('diagnostics_runtime.system_routes',return_value=[]):
   evidence=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root)._network_evidence(d._items);item=next(x for x in evidence['devices'] if x['host']=='192.168.1.50');self.assertTrue(item['reachable']);self.assertTrue(item['openipcVerified']);self.assertTrue(item['discovered'])
 def test_authenticated_discovery_evidence_is_exported_without_credentials(self):
  d,links,t,u=self.base();d._items=[{'id':'1','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335'}}];d._discovered=[{'host':'192.168.1.50','reachable':True,'camera':True,'openipc':True,'authRequired':False,'identityVerified':True,'identity':{'verified':True,'platform':'ssc30kq','sensor':'imx335'},'evidence':['Majestic /api/v1/config.json']}];d._manual_result={}
  with tempfile.TemporaryDirectory() as root, patch('diagnostics_runtime.interfaces',return_value=[]), patch('diagnostics_runtime.system_routes',return_value=[]):
   b=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root).build();text=repr(b);evidence=b['network']['evidence'];item=next(x for x in evidence['devices'] if x['host']=='192.168.1.50');self.assertTrue(item['openipcVerified']);self.assertTrue(item['discovered']);self.assertNotIn('password',text.lower());self.assertNotIn('credential',text.lower())
 def test_auth_required_candidate_is_not_reported_as_verified_openipc(self):
  d,links,t,u=self.base();d._discovered=[{'host':'192.168.1.60','reachable':True,'camera':True,'openipc':False,'authRequired':True,'identityVerified':False,'identity':{'verified':False},'evidence':['Majestic API requires authentication (401)']}];d._manual_result={}
  with tempfile.TemporaryDirectory() as root, patch('diagnostics_runtime.interfaces',return_value=[]), patch('diagnostics_runtime.system_routes',return_value=[]):
   evidence=DiagnosticsRuntime('2.0.12',d,links,t,u,DiagnosticEvents(),root)._network_evidence([]);item=next(x for x in evidence['devices'] if x['host']=='192.168.1.60');self.assertTrue(item['discovered']);self.assertFalse(item['openipcVerified'])
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
