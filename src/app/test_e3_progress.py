import unittest
from e3_progress import REQUIRED_E3_COMPONENTS, e3_progress

class E3ProgressTests(unittest.TestCase):
    def test_missing_components_are_reported_without_physical_claim(self):
        result = e3_progress({"selector": True})
        self.assertFalse(result["complete"])
        self.assertFalse(result["physicalEvidenceClaimed"])
        self.assertIn("dispatch", result["missingComponents"])

    def test_all_repository_components_can_complete_without_physical_claim(self):
        result = e3_progress({name: True for name in REQUIRED_E3_COMPONENTS})
        self.assertTrue(result["complete"])
        self.assertEqual(result["missingComponents"], [])
        self.assertFalse(result["physicalEvidenceClaimed"])

if __name__ == "__main__": unittest.main()
