import unittest

from PySide6.QtCore import QSettings

from backend import Station


class Settings:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.sync_status = QSettings.NoError

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass

    def status(self):
        return self.sync_status


class StationOsdSettingsTests(unittest.TestCase):
    def test_station_osd_is_enabled_by_default_and_persisted_when_changed(self):
        settings = Settings()
        station = Station(settings)

        self.assertTrue(station.osdEnabled)
        station.setOSDEnabled(False)
        self.assertFalse(station.osdEnabled)
        self.assertIs(settings.values[Station.OSD_ENABLED_KEY], False)

        restored = Station(settings)
        self.assertFalse(restored.osdEnabled)

    def test_legacy_false_setting_disables_only_station_overlay(self):
        settings = Settings({Station.OSD_ENABLED_KEY: "false"})
        station = Station(settings)

        self.assertFalse(station.osdEnabled)
        self.assertEqual(station.osdSource, "station")

    def test_enabling_station_overlay_does_not_change_source_osd_mode(self):
        station = Station(Settings({Station.OSD_ENABLED_KEY: False}))

        station.setOSDEnabled(True)

        self.assertTrue(station.osdEnabled)
        self.assertEqual(station.osdSource, "station")

    def test_osd_style_and_position_persist(self):
        settings = Settings()
        station = Station(settings)

        self.assertTrue(station.setOSDStyle(0.7, 1.2))
        self.assertTrue(station.setOSDStyle(0, 1.2))
        self.assertEqual(station.osdOpacity, 0)
        self.assertTrue(station.setOSDStyle(0.7, 1.2))
        self.assertTrue(station.setOSDPosition("bottom-right"))

        restored = Station(settings)
        self.assertEqual(restored.osdOpacity, 0.7)
        self.assertEqual(restored.osdScale, 1.2)
        self.assertEqual(restored.osdPosition, "bottom-right")

    def test_persisted_osd_changes_emit_a_safe_observation(self):
        station = Station(Settings())
        changes = []
        station.osdSettingsSaved.connect(lambda: changes.append(True))

        station.setOSDEnabled(False)
        station.setOSDStyle(0.7, 1.2)
        station.setOSDPosition("bottom-right")
        station.resetOSDStyle()

        self.assertEqual(changes, [True, True, True, True])

    def test_osd_style_rejects_out_of_range_values_and_clamps_saved_values(self):
        settings = Settings(
            {
                Station.OSD_OPACITY_KEY: 2,
                Station.OSD_SCALE_KEY: 0.1,
                Station.OSD_POSITION_KEY: "center",
            }
        )
        station = Station(settings)

        self.assertEqual(station.osdOpacity, 1)
        self.assertEqual(station.osdScale, 0.85)
        self.assertEqual(station.osdPosition, "corners")
        self.assertFalse(station.setOSDStyle(1.1, 1.0))
        self.assertFalse(station.setOSDPosition("center"))
        self.assertEqual(station.osdOpacity, 1)
        self.assertEqual(station.osdPosition, "corners")

    def test_osd_style_can_be_reset_to_defaults(self):
        settings = Settings()
        station = Station(settings)
        station.setOSDStyle(0.7, 1.2)
        station.setOSDPosition("bottom-right")

        station.resetOSDStyle()

        self.assertEqual(station.osdOpacity, Station.OSD_DEFAULT_OPACITY)
        self.assertEqual(station.osdScale, Station.OSD_DEFAULT_SCALE)
        self.assertEqual(station.osdPosition, Station.OSD_DEFAULT_POSITION)
        restored = Station(settings)
        self.assertEqual(restored.osdPosition, Station.OSD_DEFAULT_POSITION)

    def test_osd_persistence_error_is_explained(self):
        settings = Settings()
        settings.sync_status = QSettings.AccessError
        station = Station(settings)
        changes = []
        station.osdSettingsSaved.connect(lambda: changes.append(True))

        self.assertFalse(station.setOSDStyle(0.7, 1.2))
        self.assertIn("Не вдалося зберегти налаштування OSD", station.osdSettingsError)
        self.assertEqual(changes, [])

    def test_individual_positions_persist_validate_and_reset(self):
        settings = Settings()
        station = Station(settings)
        self.assertTrue(station.setOSDElementPosition("battery", 75, 35))
        self.assertFalse(station.setOSDElementPosition("unknown", 10, 10))
        self.assertFalse(station.setOSDElementPosition("battery", 101, 10))
        restored = Station(settings)
        self.assertEqual(restored.osdElements, {"battery": [75, 35]})
        restored.resetOSDStyle()
        self.assertEqual(Station(settings).osdElements, {})

    def test_individual_elements_default_toggle_persist_and_reset(self):
        settings = Settings()
        station = Station(settings)

        self.assertTrue(station.osdEnabledElements["battery"])
        self.assertFalse(station.osdEnabledElements["reticle"])
        self.assertFalse(station.osdEnabledElements["horizon"])
        self.assertTrue(station.setOSDElementEnabled("reticle", True))
        self.assertTrue(station.setOSDElementEnabled("horizon", True))
        self.assertTrue(station.setOSDElementEnabled("battery", False))
        self.assertFalse(station.setOSDElementEnabled("unknown", True))

        restored = Station(settings)
        self.assertTrue(restored.osdEnabledElements["reticle"])
        self.assertTrue(restored.osdEnabledElements["horizon"])
        self.assertFalse(restored.osdEnabledElements["battery"])

        restored.resetOSDStyle()
        defaults = Station(settings).osdEnabledElements
        self.assertFalse(defaults["reticle"])
        self.assertFalse(defaults["horizon"])
        self.assertTrue(defaults["battery"])

    def test_corrupt_element_visibility_keeps_safe_defaults(self):
        settings = Settings(
            {Station.OSD_ELEMENT_VISIBILITY_KEY: '{"battery":false,"reticle":true,"horizon":"yes","unknown":true}'}
        )
        station = Station(settings)
        self.assertFalse(station.osdEnabledElements["battery"])
        self.assertTrue(station.osdEnabledElements["reticle"])
        self.assertFalse(station.osdEnabledElements["horizon"])

    def test_corrupt_element_positions_are_ignored(self):
        settings = Settings(
            {Station.OSD_ELEMENTS_KEY: '{"battery":[3, 5], "speed":[200, 0], "gps":[true, 0], "other":[1, 1]}'}
        )
        self.assertEqual(Station(settings).osdElements, {"battery": [3, 5]})
        settings.values[Station.OSD_ELEMENTS_KEY] = "not json"
        self.assertEqual(Station(settings).osdElements, {})


if __name__ == "__main__":
    unittest.main()
