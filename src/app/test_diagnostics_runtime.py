import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from diagnostic_events import DiagnosticEvents
from diagnostics_runtime import DiagnosticsRuntime


class Obj:
    pass


class Tests(unittest.TestCase):
    def base(self):
        d = Obj()
        d._items = []
        links = Obj()
        links.snapshot = {'network': {'state': 'unavailable'}}
        links.changed = Obj()
        links.changed.emit = lambda: None
        t = Obj()
        t.name = 'MSP'
        t.available = False
        t.error = ''
        t.telemetry = {}
        u = Obj()
        u.updateState = 'idle'
        u.updateStatus = 'Готово'
        u.availableVersion = ''
        u.progress = 0
        return d, links, t, u

    def test_runtime_collects_real_boundaries_without_inventing_values(self):
        d, links, t, u = self.base()
        d._items = [{'id': '1', 'firmware': None, 'password': 'secret'}]
        links.snapshot = {'network': {'state': 'ready'}}
        t.name = 'MAVLink'
        t.telemetry = {'connected': None}
        with tempfile.TemporaryDirectory() as root:
            r = DiagnosticsRuntime('2.0.12', d, links, t, u, DiagnosticEvents(), root)
            b = r.build()
            self.assertIsNone(b['devices'][0]['firmware'])
            self.assertEqual(b['devices'][0]['password'], '[redacted]')
            self.assertIsNone(b['protocols']['telemetry']['connected'])

    def test_snapshot_keeps_one_runtime_correlation_identity(self):
        d, links, t, u = self.base()
        with tempfile.TemporaryDirectory() as root:
            r = DiagnosticsRuntime('2.0.12', d, links, t, u, DiagnosticEvents(), root)
            first = r.build()
            second = r.build()
            self.assertTrue(first['correlationId'])
            self.assertEqual(second['correlationId'], first['correlationId'])

    def test_export_stages_are_unique_and_preserve_capture_identity(self):
        d, links, t, u = self.base()
        with tempfile.TemporaryDirectory() as root:
            r = DiagnosticsRuntime('2.0.12', d, links, t, u, DiagnosticEvents(), root)
            a = Path(r.exportStage('hardware-e2e-preflight'))
            b = Path(r.exportStage('hardware-e2e-post-update'))
            self.assertNotEqual(a, b)
            self.assertTrue(a.is_file())
            self.assertTrue(b.is_file())
            pa = json.loads(a.read_text(encoding='utf-8'))
            pb = json.loads(b.read_text(encoding='utf-8'))
            self.assertEqual(pa['capture']['label'], 'hardware-e2e-preflight')
            self.assertEqual(pb['capture']['label'], 'hardware-e2e-post-update')
            self.assertEqual(pa['correlationId'], pb['correlationId'])

    def test_manual_probe_contributes_fresh_device_evidence(self):
        d, links, t, u = self.base()
        d._items = [{'id': '1', 'host': '192.168.1.50', 'openipcIdentity': {'verified': True}}]
        d._discovered = []
        d._manual_result = {'host': '192.168.1.50', 'reachable': True, 'openipc': True, 'identity': {'verified': True}}
        with (
            tempfile.TemporaryDirectory() as root,
            patch('diagnostics_runtime.interfaces', return_value=[]),
            patch('diagnostics_runtime.system_routes', return_value=[]),
        ):
            evidence = DiagnosticsRuntime('2.0.12', d, links, t, u, DiagnosticEvents(), root)._network_evidence(
                d._items
            )
            item = next(x for x in evidence['devices'] if x['host'] == '192.168.1.50')
            self.assertTrue(item['reachable'])
            self.assertTrue(item['openipcVerified'])
            self.assertTrue(item['discovered'])

    def test_export_creates_bundle(self):
        d, links, t, u = self.base()
        with tempfile.TemporaryDirectory() as root:
            r = DiagnosticsRuntime('2.0.12', d, links, t, u, DiagnosticEvents(), root)
            p = Path(r.export())
            self.assertTrue(p.is_file())
            self.assertEqual(p.parent.name, 'diagnostics')

    def test_only_allowlisted_non_mutating_action_executes(self):
        d, links, t, u = self.base()
        with tempfile.TemporaryDirectory() as root:
            r = DiagnosticsRuntime('2.0.12', d, links, t, u, DiagnosticEvents(), root)
            self.assertTrue(r.applyRemediation('refresh-network'))
            self.assertFalse(r.applyRemediation('shell'))
            self.assertFalse(r.applyRemediation('set-static-ip'))
            self.assertEqual(r.build()['lastRemediation']['action'], 'refresh-network')


if __name__ == '__main__':
    unittest.main()
