from source_text import read_source
from pathlib import Path
import unittest


class Tests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.qml = (root / 'HardwareE2EPanel.qml').read_text(encoding='utf-8')
        self.main = (root / 'Main.qml').read_text(encoding='utf-8')
        self.bootstrap = read_source(root / 'main.py')

    def test_panel_exposes_preflight_without_destructive_execution(self):
        self.assertIn('hardwareE2ERuntime.readiness', self.qml)
        self.assertIn('capture("preflight")', self.qml)
        self.assertNotIn('firmwareUpdateSession.execute', self.qml)
        self.assertNotIn('sysupgrade', self.qml)

    def test_update_confirmation_does_not_claim_to_accept_connection_keys(self):
        for qml in (self.qml, (Path(__file__).parent / 'FirmwareCenter.qml').read_text(encoding='utf-8')):
            self.assertIn('Підтверджую оновлення вибраної камери', qml)
            self.assertIn('confirmDeviceUpdate(checked)', qml)
            self.assertIn('не змушує програму довіряти невідомому пристрою', qml)

    def test_artifact_and_plan_are_visible_preflight_gates(self):
        self.assertIn('ready.checks.firmwareArtifactVerified', self.qml)
        self.assertIn('ready.checks.executionPlanReady', self.qml)
        self.assertIn('ready.artifact.sha256', self.qml)

    def test_panel_supports_distinct_e2e_evidence_stages(self):
        self.assertIn('capture("preflight")', self.qml)
        self.assertIn('capture("post-update")', self.qml)
        self.assertIn('capture("failure")', self.qml)
        self.assertIn('hardwareE2ERuntime.captures', self.qml)
        self.assertIn('hardwareE2ERuntime.evidenceReadiness', self.qml)

    def test_main_wires_preflight_panel_without_destructive_execution(self):
        self.assertIn('Hardware E2E', self.main)
        self.assertIn('HardwareE2EPanel', self.main)
        self.assertIn('hardwareE2EPopup.open()', self.main)
        self.assertIn('onOpened:hardwareE2ERuntime.reset()', self.main)
        self.assertNotIn('onClosed:hardwareE2ERuntime.reset()', self.main)

    def test_runtime_is_registered_and_bound_to_firmware_lifecycle(self):
        self.assertIn('HardwareE2ERuntime(d,diag,credentials,fw,fwsession)', self.bootstrap)
        self.assertIn("('hardwareE2ERuntime',hardware_e2e)", self.bootstrap)

    def test_panel_has_local_close_path(self):
        self.assertIn('signal closeRequested()', self.qml)
        self.assertIn('onClicked:closeRequested()', self.qml)


if __name__ == '__main__':
    unittest.main()
