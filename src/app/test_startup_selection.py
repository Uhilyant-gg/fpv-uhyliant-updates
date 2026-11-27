import unittest
from startup_selection import select_startup_camera

VERIFIED = ["reachable-service", "camera-candidate", "verified-openipc"]


class StartupSelectionTests(unittest.TestCase):
    def test_no_verified_camera_requests_discovery(self):
        result = select_startup_camera([{"host": "192.168.1.10", "verified": False, "evidence": ["onvif"]}])
        self.assertIsNone(result["selected"])
        self.assertEqual(result["action"], "find-camera")

    def test_single_verified_camera_is_selected(self):
        result = select_startup_camera(
            [{"host": "192.168.1.10", "verified": True, "id": "cam-a", "evidence": VERIFIED}]
        )
        self.assertEqual(result["selected"]["host"], "192.168.1.10")
        self.assertEqual(result["action"], "connect-camera")

    def test_multiple_verified_hosts_fail_closed(self):
        result = select_startup_camera(
            [
                {"host": "192.168.1.10", "verified": True, "evidence": VERIFIED},
                {"host": "192.168.1.20", "verified": True, "evidence": VERIFIED},
            ]
        )
        self.assertIsNone(result["selected"])
        self.assertIsNone(result["action"])
        self.assertEqual(result["reasonCode"], "camera-selection-ambiguous")

    def test_duplicate_same_host_is_not_ambiguous(self):
        result = select_startup_camera(
            [
                {"host": "192.168.1.10", "verified": True, "evidence": VERIFIED},
                {"host": "192.168.1.10", "verified": True, "evidence": VERIFIED},
            ]
        )
        self.assertEqual(result["selected"]["host"], "192.168.1.10")


if __name__ == "__main__":
    unittest.main()
