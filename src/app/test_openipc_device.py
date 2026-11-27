import unittest
from openipc_device import normalize_openipc_identity


class OpenIPCIdentityTests(unittest.TestCase):
    def test_generic_onvif_is_not_openipc(self):
        identity = normalize_openipc_identity({"platform": "ssc30kq"}, ["ONVIF WS-Discovery"])
        self.assertFalse(identity["verified"])
        self.assertEqual(identity["platform"], "")

    def test_verified_identity_keeps_only_observed_values(self):
        identity = normalize_openipc_identity(
            {"platform": "ssc30kq", "sensor": "imx335", "firmware": "2.4"}, ["Majestic /api/v1/config.json"]
        )
        self.assertTrue(identity["verified"])
        self.assertEqual(identity["platform"], "ssc30kq")
        self.assertEqual(identity["sensor"], "imx335")
        self.assertEqual(identity["firmware"], "2.4")
        self.assertEqual(identity["soc"], "")
        self.assertEqual(identity["majestic"], "")


if __name__ == "__main__":
    unittest.main()
