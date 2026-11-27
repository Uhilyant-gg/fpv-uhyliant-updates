from pathlib import Path
import re
import unittest


class QmlUiPolicyAuditTests(unittest.TestCase):
    def setUp(self):
        self.qml = {
            path.name: path.read_text(encoding="utf-8")
            for path in Path(__file__).parent.glob("*.qml")
        }

    def visible_literals(self, source):
        return "\n".join(
            re.findall(r'(?:text|placeholderText|title)\s*:\s*"([^"]*)"', source)
        )

    def test_all_expected_qml_surfaces_are_audited(self):
        self.assertEqual(
            set(self.qml),
            {
                "BackupPanel.qml",
                "DevicesPanel.qml",
                "DiagnosticsPanel.qml",
                "FirmwareCenter.qml",
                "HardwareE2EPanel.qml",
                "HomePanel.qml",
                "HoverHint.qml",
                "Main.qml",
                "MavlinkDiagnostics.qml",
                "OsdOverlay.qml",
                "OsdSettingsPanel.qml",
                "PairingPanel.qml",
                "PreflightPanel.qml",
                "TimelinePanel.qml",
                "UpdatePanel.qml",
            },
        )

    def test_visible_ui_does_not_restore_known_english_copy(self):
        obsolete = (
            "SERVICE MODE", "VIDEO WORKSPACE", "Primary", "Secondary", "Swap",
            "Firmware", "Telemetry:", "Network:", "IDENTITY", "System / Component",
            "Vehicle", "System state", "LINK DIAGNOSTICS", "Health", "Message rate",
            "Last packet", "Estimated lost", "Bad data", "Comm errors",
            "Controller load", "not broadcast", "Manifest", "Expected SHA-256",
            "Camera preset", "video profile", "hardware apply",
        )
        for name, source in self.qml.items():
            visible = self.visible_literals(source)
            for phrase in obsolete:
                with self.subTest(file=name, phrase=phrase):
                    self.assertNotIn(phrase, visible)

    def test_shared_hover_hint_contract_is_five_seconds(self):
        hint = self.qml["HoverHint.qml"]
        self.assertIn("property int delay:5000", hint)
        self.assertIn("showTimer.restart()", hint)
        self.assertIn("tip.close()", hint)

    def test_pairing_security_boundary_remains_fail_closed(self):
        pairing = self.qml["PairingPanel.qml"]
        self.assertNotIn("pairingRegistry.begin(", pairing)
        self.assertNotIn("pairingRegistry.confirm(", pairing)
        self.assertNotIn("secretRef", pairing)


if __name__ == "__main__":
    unittest.main()
