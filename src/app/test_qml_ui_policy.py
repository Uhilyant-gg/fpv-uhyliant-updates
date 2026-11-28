from pathlib import Path
import re
import unittest


class QmlUiPolicyAuditTests(unittest.TestCase):
    def setUp(self):
        self.qml = {path.name: path.read_text(encoding="utf-8") for path in Path(__file__).parent.glob("*.qml")}

    def visible_literals(self, source):
        return "\n".join(re.findall(r'(?:text|placeholderText|title)\s*:\s*"([^"]*)"', source))

    def test_all_expected_qml_surfaces_are_audited(self):
        self.assertEqual(
            set(self.qml),
            {
                "ArchiveDialog.qml",
                "BackupPanel.qml",
                "CameraSettingsDialog.qml",
                "ControllerPanel.qml",
                "DevicesPanel.qml",
                "DiagnosticsPanel.qml",
                "FlightBar.qml",
                "FirmwareCenter.qml",
                "HardwareE2EPanel.qml",
                "HardwarePanel.qml",
                "LinkGraph.qml",
                "StarlinkPanel.qml",
                "HomePanel.qml",
                "HoverHint.qml",
                "Main.qml",
                "MavlinkDiagnostics.qml",
                "OsdOverlay.qml",
                "OsdSettingsPanel.qml",
                "PairingPanel.qml",
                "PreflightPanel.qml",
                "PresetsPanel.qml",
                "RecordingPanel.qml",
                "TabbedHub.qml",
                "TimelinePanel.qml",
                "ZeroTierPanel.qml",
                "UpdatePanel.qml",
            },
        )

    def test_visible_ui_does_not_restore_known_english_copy(self):
        obsolete = (
            "SERVICE MODE",
            "VIDEO WORKSPACE",
            "Primary",
            "Secondary",
            "Swap",
            "Firmware",
            "Telemetry:",
            "Network:",
            "IDENTITY",
            "System / Component",
            "Vehicle",
            "System state",
            "LINK DIAGNOSTICS",
            "Health",
            "Message rate",
            "Last packet",
            "Estimated lost",
            "Bad data",
            "Comm errors",
            "Controller load",
            "not broadcast",
            "Manifest",
            "Expected SHA-256",
            "Camera preset",
            "video profile",
            "hardware apply",
        )
        for name, source in self.qml.items():
            visible = self.visible_literals(source)
            for phrase in obsolete:
                with self.subTest(file=name, phrase=phrase):
                    self.assertNotIn(phrase, visible)

    def test_osd_distinguishes_stale_fields_from_unavailable_values(self):
        source = self.qml["OsdOverlay.qml"]
        self.assertIn("telemetry.freshness", source)
        self.assertIn('"застаріло"', source)
        self.assertIn("optionalTelemetryText", source)

    def test_osd_preview_can_check_common_aspect_ratios_and_explains_layout_issues(self):
        source = self.qml["OsdSettingsPanel.qml"]
        for label in ("Широкий 16:9", "Класичний 4:3", "Квадрат 1:1", "Вертикальний 9:16"):
            self.assertIn(label, source)
        self.assertIn("previewHost.height * aspectRatio", source)
        self.assertIn("previewHost.width / aspectRatio", source)
        self.assertIn("Перетягніть позначені елементи по сітці", source)
        self.assertIn("Розташування не змінюється автоматично", source)

    def test_osd_controls_explain_camera_pixels_cannot_be_removed(self):
        copy = "\n".join(
            self.visible_literals(self.qml[name]) for name in ("Main.qml", "OsdSettingsPanel.qml", "PreflightPanel.qml")
        )
        self.assertIn("вбудоване в зображення", copy)
        self.assertIn("прибрати його тут неможливо", copy)
        self.assertIn("Додавати OSD станції поверх відео", copy)
        self.assertNotIn("Вимкнути OSD камери", copy)

    def test_osd_layout_editing_locks_when_telemetry_reports_armed(self):
        main = self.qml["Main.qml"]
        panel = self.qml["OsdSettingsPanel.qml"]
        main = re.sub(r"\s+", "", main)
        self.assertIn(
            "functionopenOsdSettings(){if(!osdSettingsLoader.active){osdSettingsLoader.active=true;Qt.callLater(openOsdSettings);return}osdSettingsLoader.item.editingAllowed=w.simulation||t.armed!==true;osdSettingsPopup.open()}",
            main,
        )
        self.assertIn(
            "if(osdSettingsPopup.visible&&!w.simulation&&osdSettingsLoader.item)osdSettingsLoader.item.editingAllowed=t.armed!==true",
            main,
        )
        self.assertNotIn("editingAllowed:w.simulation||t.armed!==true", main)
        self.assertIn("enabled: root.editingAllowed", panel)
        self.assertIn("editing: root.editingAllowed", panel)
        self.assertIn("Телеметрія показує ARM", panel)

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
