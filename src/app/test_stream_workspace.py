import unittest
from stream_workspace import StreamWorkspace
class Devices:
 activeStreams=[{"id":"main","kind":"main","enabled":True},{"id":"sub","kind":"sub","enabled":True},{"id":"thermal","kind":"thermal","enabled":True}]
class OneStream:
 activeStreams=[{"id":"main","kind":"main","enabled":True}]
class MissingStream:
 activeStreams=[]
class Tests(unittest.TestCase):
 def test_auto_selects_real_main_and_secondary(self):
  w=StreamWorkspace(Devices());w.autoSelect();self.assertEqual(w.state["primaryId"],"main");self.assertEqual(w.state["secondaryId"],"sub");self.assertTrue(w.state["pipAvailable"])
 def test_pip_unavailable_with_one_stream(self):
  w=StreamWorkspace(OneStream());w.autoSelect();self.assertEqual(w.state["primaryId"],"main");self.assertEqual(w.state["secondaryId"],"");self.assertFalse(w.state["pipAvailable"])
 def test_missing_stream_remains_unavailable(self):
  w=StreamWorkspace(MissingStream());w.autoSelect();self.assertEqual(w.state["primaryId"],"");self.assertEqual(w.state["secondaryId"],"");self.assertFalse(w.state["pipAvailable"])
 def test_cannot_select_unknown_or_same_secondary(self):
  w=StreamWorkspace(Devices());w.autoSelect();self.assertFalse(w.selectPrimary("missing"));self.assertFalse(w.selectSecondary("main"))
 def test_swap_uses_existing_streams_only(self):
  w=StreamWorkspace(Devices());w.autoSelect();before={s['id'] for s in Devices.activeStreams};w.swap();self.assertEqual(w.state["primaryId"],"sub");self.assertEqual(w.state["secondaryId"],"main");self.assertIn(w.state["primaryId"],before);self.assertIn(w.state["secondaryId"],before)
if __name__=="__main__":unittest.main()
