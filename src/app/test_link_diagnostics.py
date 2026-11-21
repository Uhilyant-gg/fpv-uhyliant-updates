import unittest
from link_diagnostics import LinkDiagnostics
class Clock:
 def __init__(self):self.now=10.0
 def __call__(self):return self.now
class Tests(unittest.TestCase):
 def test_unknown_is_unavailable_not_zero(self):
  d=LinkDiagnostics();self.assertFalse(d.network['available']);self.assertIsNone(d.network['rttMs']);self.assertFalse(d.externalNavigation['available']);self.assertIsNone(d.externalNavigation['quality'])
 def test_observations_remain_separate(self):
  d=LinkDiagnostics();d.observeExternalNavigation('StabX','ready','tracking','observed packet');d.observeNetwork('WireGuard','ready','wg0','10.5.0.1',32.5,'observed probe');self.assertEqual(d.externalNavigation['source'],'StabX');self.assertEqual(d.network['transport'],'WireGuard');self.assertEqual(d.network['rttMs'],32.5)
 def test_invalid_network_does_not_invent_rtt(self):
  d=LinkDiagnostics();d.observeNetwork('Starlink','ready','','',-1,'');self.assertFalse(d.network['available']);self.assertIsNone(d.network['rttMs'])
 def test_observation_becomes_stale(self):
  c=Clock();d=LinkDiagnostics(c,5);d.observeExternalNavigation('StabX','ready','tracking','');c.now=16;self.assertEqual(d.externalNavigation['state'],'stale');self.assertFalse(d.externalNavigation['available'])
 def test_clear_removes_observed_values(self):
  d=LinkDiagnostics();d.observeNetwork('WireGuard','ready','wg0','peer',1,'');d.clear();self.assertIsNone(d.network['rttMs']);self.assertEqual(d.network['state'],'unavailable')
if __name__=='__main__':unittest.main()
