import threading
import unittest
from unittest.mock import patch
from route_discovery import fingerprint, plan_targets, route_is_sweepable


class RouteDiscoveryTests(unittest.TestCase):
    def test_routed_camera_regression(self):
        interfaces = [{"name": "Wi-Fi", "network": "192.168.0.0/24"}]
        routes = [{"name": "192.168.0.1", "network": "192.168.1.0/24"}]
        targets = plan_targets(interfaces, routes)
        self.assertIn("192.168.1.50", targets)
        self.assertIn("192.168.0.12", targets)

    def test_unsafe_and_large_routes_are_not_swept(self):
        routes = [
            {"name": "Wi-Fi", "network": "0.0.0.0/0"},
            {"name": "Wi-Fi", "network": "8.8.8.0/24"},
            {"name": "Wi-Fi", "network": "10.0.0.0/8"},
            {"name": "vEthernet (WSL)", "network": "172.20.0.0/24"},
        ]
        self.assertEqual(plan_targets([], routes), [])
        self.assertFalse(route_is_sweepable("10.0.0.0/8", "Wi-Fi"))

    def test_known_private_host_is_direct_even_without_sweep(self):
        self.assertEqual(plan_targets([], [], ["192.168.1.50"]), ["192.168.1.50"])

    @patch("route_discovery._fetch")
    def test_generic_onvif_or_reachable_host_is_not_openipc(self, fetch):
        fetch.return_value = b"<html>generic camera</html>"
        result = fingerprint("192.168.1.50", threading.Event())
        self.assertFalse(result["openipc"])
        self.assertFalse(result["camera"])
        self.assertFalse(result["identityVerified"])

    @patch("route_discovery._fetch")
    def test_status_cgi_observations_are_preserved_without_defaults(self, fetch):
        def response(url, *args):
            if url.endswith("config.json"): return None
            return b"OpenIPC Majestic Platform: ssc30kq Sensor: imx335 Firmware: v1.48.5.1-st-ultimate"
        fetch.side_effect = response
        result = fingerprint("192.168.1.50", threading.Event())
        self.assertTrue(result["openipc"])
        self.assertEqual(result["identity"]["platform"], "ssc30kq")
        self.assertEqual(result["identity"]["sensor"], "imx335")
        self.assertEqual(result["identity"]["soc"], "")


if __name__ == "__main__": unittest.main()
