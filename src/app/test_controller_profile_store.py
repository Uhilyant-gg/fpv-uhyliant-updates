import json
import tempfile
import unittest
from pathlib import Path

from controller_profile import calibrate_controller, validate_controller_profile
from controller_profile_store import ControllerProfileStoreInvalid, JsonControllerProfileStore

MAPPING = {
    "roll": {"channel": 0, "reversed": False},
    "pitch": {"channel": 1, "reversed": False},
    "yaw": {"channel": 2, "reversed": False},
    "throttle": {"channel": 3, "reversed": False},
}
SAMPLES = [[1000] * 4, [1500] * 4, [2000] * 4]


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "controllers.json"
        self.store = JsonControllerProfileStore(self.path)
        self.profile = calibrate_controller("radio-1", SAMPLES, MAPPING)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_is_empty(self):
        self.assertEqual(self.store.load(), {})

    def test_round_trip_persists_only_non_secret_profile(self):
        self.store.save_profile("radio-1", "EdgeTX", self.profile)
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(set(raw["records"][0]), {"id", "name", "profile"})
        loaded = JsonControllerProfileStore(self.path).load()
        self.assertEqual(loaded["radio-1"]["profile"], self.profile)
        self.assertFalse(self.path.with_suffix(".json.tmp").exists())

    def test_profile_must_be_bound_to_record_identity(self):
        with self.assertRaises(ControllerProfileStoreInvalid):
            self.store.save_profile("radio-2", None, self.profile)

    def test_corrupt_file_fails_closed_and_is_not_overwritten(self):
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(ControllerProfileStoreInvalid):
            self.store.load()
        with self.assertRaises(ControllerProfileStoreInvalid):
            self.store.save_profile("radio-1", None, self.profile)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not json")

    def test_extra_fields_or_tampered_profiles_are_rejected(self):
        self.store.save_profile("radio-1", None, self.profile)
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        raw["records"][0]["password"] = "x"
        self.path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(ControllerProfileStoreInvalid):
            self.store.load()
        del raw["records"][0]["password"]
        raw["records"][0]["profile"]["calibration"][0]["center"] = 5000
        self.path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(ControllerProfileStoreInvalid):
            self.store.load()

    def test_forget_removes_record(self):
        self.store.save_profile("radio-1", None, self.profile)
        self.assertTrue(self.store.forget("radio-1"))
        self.assertFalse(self.store.forget("radio-1"))
        self.assertEqual(self.store.load(), {})


class ValidateProfileTests(unittest.TestCase):
    def test_valid_profile_round_trips(self):
        profile = calibrate_controller("radio-1", SAMPLES, MAPPING)
        self.assertEqual(validate_controller_profile(profile), profile)

    def test_unknown_keys_and_bad_mapping_are_invalid(self):
        profile = calibrate_controller("radio-1", SAMPLES, MAPPING)
        for bad in ({**profile, "extra": 1}, {**profile, "mapping": {}}, {**profile, "schemaVersion": 2}, None):
            with self.assertRaisesRegex(ValueError, "controller-profile-invalid"):
                validate_controller_profile(bad)


if __name__ == "__main__":
    unittest.main()
