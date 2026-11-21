import unittest
from network_evidence import collect_network_evidence
class Tests(unittest.TestCase):
 def test_evidence_separates_safe_routes_and_virtual_or_public(self):
  interfaces=[{'name':'Ethernet','address':'192.168.1.10','network':'192.168.1.0/24'},{'name':'docker0','address':'172.17.0.1','network':'172.17.0.0/24'}]
  routes=[{'network':'192.168.1.0/24','interface':'Ethernet'},{'network':'8.8.8.0/24','interface':'Ethernet'}]
  e=collect_network_evidence(interfaces,routes);self.assertEqual(e['summary']['usableInterfaces'],1);self.assertEqual(e['summary']['safeRoutes'],1)
 def test_saved_and_discovered_device_evidence_is_merged(self):
  saved=[{'host':'192.168.1.20','openipcIdentity':{'verified':True}}];found=[{'host':'192.168.1.20','reachable':True,'openipc':True}]
  e=collect_network_evidence([],[],saved,found);self.assertEqual(len(e['devices']),1);self.assertTrue(e['devices'][0]['saved']);self.assertTrue(e['devices'][0]['discovered']);self.assertTrue(e['devices'][0]['reachable']);self.assertTrue(e['devices'][0]['openipcVerified'])
 def test_invalid_hosts_do_not_become_evidence(self):
  e=collect_network_evidence([],[],[{'host':'bad'}],[{'host':'also-bad','reachable':True}]);self.assertEqual(e['devices'],[]);self.assertEqual(e['summary']['knownDevices'],0)
if __name__=='__main__':unittest.main()
