import unittest
from stream_workspace import StreamWorkspace
class Devices:
 activeStreams=[{"id":"main","kind":"main","enabled":True},{"id":"sub","kind":"sub","enabled":True},{"id":"thermal","kind":"thermal","enabled":True}]
class Tests(unittest.TestCase):
 def test_auto_selects_real_main_and_secondary(self):
  w=StreamWorkspace(Devices());w.autoSelect();self.assertEqual(w.state["primaryId"],"main");self.assertEqual(w.state["secondaryId"],"sub");self.assertTrue(w.state["pipAvailable"])
 def test_cannot_select_unknown_or_same_secondary(self):
  w=StreamWorkspace(Devices());w.autoSelect();self.assertFalse(w.selectPrimary("missing"));self.assertFalse(w.selectSecondary("main"))
 def test_swap_uses_existing_streams_only(self):
  w=StreamWorkspace(Devices());w.autoSelect();w.swap();self.assertEqual(w.state["primaryId"],"sub");self.assertEqual(w.state["secondaryId"],"main")
if __name__=="__main__":unittest.main()
