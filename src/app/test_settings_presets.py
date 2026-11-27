import json
import tempfile
import unittest
from pathlib import Path

from settings_presets import PresetError, PresetStore
from station_settings import default_settings, validate_station_settings


def custom_settings():
    settings = default_settings()
    settings["osd"]["opacity"] = 0.4
    settings["osd"]["elements"] = {"battery": [10, 80]}
    settings["alerts"]["cellCount"] = 6
    return settings


class StationSettingsTests(unittest.TestCase):
    def test_missing_keys_take_defaults_and_unknown_keys_are_ignored(self):
        result = validate_station_settings({"osd": {"opacity": 0.3, "future": 1}, "extra": {}})
        self.assertEqual(result["osd"]["opacity"], 0.3)
        self.assertEqual(result["alerts"], default_settings()["alerts"])

    def test_invalid_present_values_reject_everything(self):
        for bad in (
            None,
            {"osd": {"opacity": 2}},
            {"osd": {"position": "middle"}},
            {"osd": {"elements": {"battery": [10, 101]}}},
            {"osd": {"elementVisibility": {"gps": "yes"}}},
            {"alerts": {"linkQualityMin": -1}},
            {"osd": []},
        ):
            with self.assertRaises(ValueError, msg=bad):
                validate_station_settings(bad)


class PresetStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.store = PresetStore(self.dir / "presets.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_activate_and_reload(self):
        preset = self.store.create("  Квадрик 5\"  ", custom_settings())
        state = PresetStore(self.dir / "presets.json").load()
        self.assertEqual(state["active"], preset["id"])
        self.assertEqual(state["presets"][0]["name"], 'Квадрик 5"')
        self.assertEqual(state["presets"][0]["settings"]["alerts"]["cellCount"], 6)

    def test_duplicate_names_get_suffix_and_rename_rejects_taken_name(self):
        a = self.store.create("Крило", default_settings())
        b = self.store.create("крило", default_settings())
        self.assertEqual(b["name"], "крило (2)")
        with self.assertRaisesRegex(PresetError, "taken"):
            self.store.rename(b["id"], "КРИЛО")
        self.assertEqual(self.store.rename(a["id"], "Крило 7\"")["name"], 'Крило 7"')
        with self.assertRaisesRegex(PresetError, "name-invalid"):
            self.store.rename(a["id"], "   ")

    def test_copy_is_independent(self):
        source = self.store.create("Квадрик", custom_settings())
        copy = self.store.duplicate(source["id"])
        self.assertEqual(copy["name"], "Квадрик (копія)")
        self.assertNotEqual(copy["id"], source["id"])
        changed = default_settings()
        self.store.save_settings(copy["id"], changed)
        state = self.store.load()
        by_id = {p["id"]: p for p in state["presets"]}
        self.assertEqual(by_id[source["id"]]["settings"]["osd"]["opacity"], 0.4)
        self.assertEqual(by_id[copy["id"]]["settings"]["osd"]["opacity"], default_settings()["osd"]["opacity"])

    def test_delete_clears_active(self):
        preset = self.store.create("A", default_settings())
        self.store.delete(preset["id"])
        self.assertEqual(self.store.load(), {"active": None, "presets": []})
        with self.assertRaisesRegex(PresetError, "not-found"):
            self.store.delete(preset["id"])

    def test_export_import_round_trip_gets_new_id(self):
        preset = self.store.create("Квадрик", custom_settings())
        path = self.dir / "квадрик.fpvpreset"
        self.store.export(preset["id"], path)
        other = PresetStore(self.dir / "other.json")
        imported = other.import_file(path)
        self.assertEqual(imported["name"], "Квадрик")
        self.assertEqual(imported["settings"], preset["settings"])
        again = self.store.import_file(path)
        self.assertNotEqual(again["id"], preset["id"])
        self.assertEqual(again["name"], "Квадрик (2)")

    def test_bad_import_files_are_rejected_without_changes(self):
        cases = {
            "garbage.json": "{not json",
            "schema.json": json.dumps({"schema": "x", "version": 1, "name": "A", "settings": {}}),
            "settings.json": json.dumps(
                {"schema": "fpv-uhyliant-preset", "version": 1, "name": "A", "settings": {"osd": {"scale": 9}}}
            ),
            "name.json": json.dumps({"schema": "fpv-uhyliant-preset", "version": 1, "name": "", "settings": {}}),
        }
        for filename, content in cases.items():
            path = self.dir / filename
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(PresetError, "file-invalid", msg=filename):
                self.store.import_file(path)
        self.assertEqual(self.store.load()["presets"], [])

    def test_corrupt_store_is_reported_and_not_overwritten(self):
        (self.dir / "presets.json").write_text("{bad", encoding="utf-8")
        with self.assertRaisesRegex(PresetError, "store-invalid"):
            self.store.create("A", default_settings())
        self.assertEqual((self.dir / "presets.json").read_text(encoding="utf-8"), "{bad")


if __name__ == "__main__":
    unittest.main()
