import unittest
from firmware_status_presentation import firmware_status

class FirmwareStatusPresentationTests(unittest.TestCase):
    def test_missing_state_is_unknown(self):
        self.assertFalse(firmware_status(None)["ready"])

    def test_only_verified_bound_selection_exposes_update(self):
        value={"state":"verified","selection":{"ready":True,"artifact":{"sha256":"a"*64}}}
        result=firmware_status(value)
        self.assertTrue(result["ready"]);self.assertEqual(result["action"],"update")

    def test_catalog_ready_without_verified_artifact_cannot_update(self):
        result=firmware_status({"state":"ready","selection":{}})
        self.assertFalse(result["ready"]);self.assertIsNone(result["action"])

if __name__ == "__main__": unittest.main()
