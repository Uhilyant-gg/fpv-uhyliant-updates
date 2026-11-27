import unittest
from controller_input_health import controller_input_health
class Tests(unittest.TestCase):
 def test_absent_controller_unknown(self):self.assertEqual(controller_input_health(None)['health'],'unknown')
 def test_connected_without_channels_unknown(self):self.assertEqual(controller_input_health({'connected':True})['channelCount'],None)
 def test_non_numeric_channel_problem(self):self.assertEqual(controller_input_health({'connected':True,'channels':[1500,None]})['health'],'problem')
 def test_non_finite_and_boolean_channels_are_problem(self):
  for value in (float('nan'),float('inf'),True,10**10000):
   with self.subTest(value=value):self.assertEqual(controller_input_health({'connected':True,'channels':[value]})['health'],'problem')
 def test_observed_numeric_channels_ready(self):
  r=controller_input_health({'connected':True,'channels':[1000,1500,2000]});self.assertEqual(r['health'],'ready');self.assertEqual(r['channelCount'],3)
if __name__=='__main__':unittest.main()
