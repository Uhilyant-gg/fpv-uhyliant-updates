import threading,unittest
from unittest.mock import patch
from route_discovery import _http_url,fingerprint,plan_targets,route_is_sweepable
class RouteDiscoveryTests(unittest.TestCase):
 def test_routed_camera_regression(self):
  targets=plan_targets([{"name":"Wi-Fi","network":"192.168.0.0/24"}],[{"name":"192.168.0.1","network":"192.168.1.0/24"}]);self.assertIn("192.168.1.50",targets);self.assertIn("192.168.0.12",targets)
 def test_unsafe_and_large_routes_are_not_swept(self):
  routes=[{"name":"Wi-Fi","network":"0.0.0.0/0"},{"name":"Wi-Fi","network":"8.8.8.0/24"},{"name":"Wi-Fi","network":"10.0.0.0/8"},{"name":"vEthernet (WSL)","network":"172.20.0.0/24"}];self.assertEqual(plan_targets([],routes),[]);self.assertFalse(route_is_sweepable("10.0.0.0/8","Wi-Fi"))
 def test_all_rfc1918_24_routes_are_sweepable_but_public_linklocal_and_virtual_are_not(self):
  for network in ("10.20.30.0/24","172.16.44.0/24","192.168.77.0/24"):self.assertTrue(route_is_sweepable(network,"Ethernet"),network)
  for network,name in (("100.64.1.0/24","Ethernet"),("169.254.2.0/24","Ethernet"),("192.168.1.0/24","WireGuard Tunnel")):self.assertFalse(route_is_sweepable(network,name),(network,name))
 def test_known_private_host_is_direct_even_without_sweep(self):self.assertEqual(plan_targets([],[],["192.168.1.50"]),["192.168.1.50"])
 def test_real_endpoint_builder_uses_observed_ipv4_and_fixed_paths(self):
  self.assertTrue(_http_url("192.168.1.50","/api/v1/config.json").endswith("192.168.1.50/api/v1/config.json"));self.assertTrue(_http_url("192.168.1.50","/cgi-bin/status.cgi").endswith("192.168.1.50/cgi-bin/status.cgi"));self.assertNotIn("scrubbed",_http_url("192.168.1.50","/cgi-bin/status.cgi"))
 @patch("route_discovery._fetch")
 def test_generic_onvif_or_reachable_host_is_not_openipc(self,fetch):
  fetch.return_value=b"<html>generic camera</html>";r=fingerprint("192.168.1.50",threading.Event());self.assertTrue(r["reachable"]);self.assertFalse(r["openipc"]);self.assertFalse(r["camera"])
 @patch("route_discovery._fetch")
 def test_status_cgi_observations_are_preserved_without_defaults(self,fetch):
  fetch.side_effect=lambda url,*args:None if url.endswith("config.json") else b"OpenIPC Majestic Platform: ssc30kq Sensor: imx335 Firmware: v1.48.5.1-st-ultimate";r=fingerprint("192.168.1.50",threading.Event());self.assertTrue(r["openipc"]);self.assertEqual(r["identity"]["platform"],"ssc30kq");self.assertEqual(r["identity"]["sensor"],"imx335");self.assertEqual(r["identity"]["soc"],"")
 @patch("route_discovery._fetch")
 def test_config_does_not_invent_stream_urls(self,fetch):
  fetch.side_effect=[b'{"video0":{"codec":"h264"},"system":{"platform":"ssc30kq"}}',None];r=fingerprint("192.168.1.50",threading.Event());self.assertTrue(r["openipc"]);self.assertEqual(r["streams"],[])
 @patch("route_discovery._fetch")
 def test_nested_generic_version_is_not_majestic_version(self,fetch):
  fetch.side_effect=[b'{"video0":{"version":"99"},"system":{"platform":"ssc30kq"}}',None];self.assertEqual(fingerprint("192.168.1.50",threading.Event())["identity"]["majestic"],"")
 @patch("route_discovery._fetch")
 def test_r2d2_marker_requires_openipc_evidence(self,fetch):
  fetch.side_effect=[None,b"R2D2 generic page"];r=fingerprint("192.168.1.50",threading.Event());self.assertFalse(r["openipc"]);self.assertFalse(r["r2d2"]);self.assertFalse(r["camera"])
if __name__=="__main__":unittest.main()
