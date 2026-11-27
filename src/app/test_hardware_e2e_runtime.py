import unittest
from hardware_e2e_runtime import HardwareE2ERuntime


class Signal:
    def __init__(self):
        self.handlers = []

    def connect(self, handler):
        self.handlers.append(handler)

    def emit(self):
        for handler in list(self.handlers):
            handler()


class Obj:
    def __init__(self):
        self.changed = Signal()


class Diagnostics(Obj):
    def __init__(self):
        super().__init__()
        self.exports = []

    def build(self):
        return {
            'network': {
                'evidence': {'summary': {'safeRoutes': 1}, 'devices': [{'host': '192.168.1.50', 'reachable': True}]}
            }
        }

    def exportStage(self, label):
        self.exports.append(label)
        return label + '.json'


class Credentials(Obj):
    def __init__(self):
        super().__init__()
        self.password = True

    def snapshot(self):
        return {'hasPassword': self.password}


class Devices(Obj):
    def __init__(self):
        super().__init__()
        self._items = [
            {
                'id': 'cam',
                'active': True,
                'host': '192.168.1.50',
                'openipcIdentity': {
                    'verified': True,
                    'platform': 'ssc30kq',
                    'sensor': 'imx335',
                    'firmware': 'old',
                    'evidence': ['OpenIPC status.cgi'],
                },
            }
        ]


class Firmware(Obj):
    def __init__(self):
        super().__init__()
        self.artifact = {'verified': True, 'sha256': 'a' * 64, 'size': 100, 'build': 'new'}
        self.executionPlan = {
            'ready': True,
            'deviceId': 'cam',
            'profile': 'ssc30kq-imx335',
            'mode': 'upgrade',
            'approvalToken': 'approval',
            'artifactSha256': 'a' * 64,
            'artifactSize': 100,
        }
        self.result = {
            'ready': True,
            'deviceId': 'cam',
            'profile': 'ssc30kq-imx335',
            'mode': 'upgrade',
            'approvalToken': 'approval',
            'artifactSha256': 'a' * 64,
        }


class Session(Obj):
    def __init__(self):
        super().__init__()
        self.result = {'state': 'ready', 'observedFirmware': '', 'verification': {}, 'transaction': {}}


class Tests(unittest.TestCase):
    def make(self):
        d = Devices()
        diag = Diagnostics()
        cred = Credentials()
        fw = Firmware()
        session = Session()
        runtime = HardwareE2ERuntime(d, diag, cred, fw, session)
        return runtime, diag, session, fw

    def ready(self, r):
        r.setHostKeyAccepted(True)
        self.assertTrue(r.readiness['ready'])

    def preflight(self, r):
        self.ready(r)
        self.assertEqual(r.capture('preflight'), 'hardware-e2e-preflight.json')

    def transaction(self, r, **extra):
        keys = ('deviceId', 'host', 'platform', 'sensor', 'artifactSha256', 'artifactSize', 'approvalToken')
        tx = dict(zip(keys, r._evidence_binding[:7]))
        tx.update(extra)
        return tx

    def test_preflight_capture_requires_complete_readiness(self):
        r, diag, _, _ = self.make()
        self.assertEqual(r.capture('preflight'), '')
        self.preflight(r)
        self.assertEqual(diag.exports, ['hardware-e2e-preflight'])

    def test_post_update_capture_requires_bound_preflight_and_verified_observed_firmware(self):
        r, diag, s, _ = self.make()
        self.ready(r)
        s.result = {
            'state': 'verified',
            'observedFirmware': 'new',
            'verification': {'ok': True, 'identity': {'firmware': 'new'}},
            'transaction': {},
        }
        s.changed.emit()
        self.assertEqual(r.capture('post-update'), '')
        self.preflight(r)
        s.result = {
            'state': 'verified',
            'observedFirmware': 'new',
            'verification': {'ok': True, 'identity': {'firmware': 'new'}},
            'transaction': self.transaction(r),
        }
        s.changed.emit()
        self.assertEqual(r.capture('post-update'), 'hardware-e2e-post-update.json')
        self.assertEqual(diag.exports, ['hardware-e2e-preflight', 'hardware-e2e-post-update'])

    def test_verified_without_observed_firmware_cannot_capture_success(self):
        r, diag, s, _ = self.make()
        self.preflight(r)
        s.result = {
            'state': 'verified',
            'observedFirmware': '',
            'verification': {'ok': True, 'identity': {}},
            'transaction': self.transaction(r),
        }
        s.changed.emit()
        self.assertFalse(r.evidenceReadiness['postUpdate'])
        self.assertEqual(r.capture('post-update'), '')
        self.assertEqual(diag.exports, ['hardware-e2e-preflight'])

    def test_failure_capture_requires_bound_executed_transaction(self):
        r, diag, s, _ = self.make()
        self.preflight(r)
        s.result = {'state': 'error', 'observedFirmware': '', 'verification': {}, 'transaction': self.transaction(r)}
        s.changed.emit()
        self.assertEqual(r.capture('failure'), 'hardware-e2e-failure.json')
        self.assertEqual(diag.exports, ['hardware-e2e-preflight', 'hardware-e2e-failure'])

    def test_blocked_without_execution_transaction_is_not_hardware_outcome(self):
        r, _, s, _ = self.make()
        self.preflight(r)
        s.result = {'state': 'blocked', 'observedFirmware': '', 'verification': {}, 'transaction': {}}
        s.changed.emit()
        self.assertFalse(r.evidenceReadiness['failure'])

    def test_reboot_pending_is_not_terminal_but_bound_error_is(self):
        r, _, s, _ = self.make()
        self.preflight(r)
        tx = self.transaction(r)
        s.result = {'state': 'reboot-pending', 'observedFirmware': '', 'verification': {}, 'transaction': tx}
        s.changed.emit()
        self.assertFalse(r.evidenceReadiness['failure'])
        s.result = {'state': 'error', 'observedFirmware': '', 'verification': {}, 'transaction': tx}
        s.changed.emit()
        self.assertTrue(r.evidenceReadiness['failure'])

    def test_mismatched_session_transaction_cannot_capture_terminal_evidence(self):
        r, diag, s, _ = self.make()
        self.preflight(r)
        s.result = {
            'state': 'error',
            'observedFirmware': '',
            'verification': {},
            'transaction': self.transaction(r, artifactSha256='b' * 64),
        }
        s.changed.emit()
        self.assertFalse(r.evidenceReadiness['failure'])
        self.assertEqual(r.capture('failure'), '')
        self.assertEqual(diag.exports, ['hardware-e2e-preflight'])

    def test_transaction_change_before_execution_invalidates_staged_evidence(self):
        r, diag, s, fw = self.make()
        self.preflight(r)
        fw.executionPlan['approvalToken'] = 'different'
        fw.changed.emit()
        self.assertEqual(r.captures, {})
        s.result = {'state': 'error', 'observedFirmware': '', 'verification': {}, 'transaction': {}}
        s.changed.emit()
        self.assertFalse(r.evidenceReadiness['failure'])
        self.assertEqual(r.capture('failure'), '')
        self.assertEqual(diag.exports, ['hardware-e2e-preflight'])


if __name__ == '__main__':
    unittest.main()
