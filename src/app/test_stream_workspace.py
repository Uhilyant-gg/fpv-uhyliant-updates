import unittest
from stream_workspace import StreamWorkspace


class Devices:
    def __init__(self):
        self.activeStreams = [
            {"id": "main", "kind": "main", "enabled": True},
            {"id": "sub", "kind": "sub", "enabled": True},
            {"id": "thermal", "kind": "thermal", "enabled": True},
        ]


class OneStream:
    activeStreams = [{"id": "main", "kind": "main", "enabled": True}]


class MissingStream:
    activeStreams = []


class Tests(unittest.TestCase):
    def test_auto_selects_real_main_and_secondary(self):
        w = StreamWorkspace(Devices())
        w.autoSelect()
        self.assertEqual(w.state["primaryId"], "main")
        self.assertEqual(w.state["secondaryId"], "sub")
        self.assertTrue(w.state["pipAvailable"])

    def test_pip_unavailable_with_one_stream(self):
        w = StreamWorkspace(OneStream())
        w.autoSelect()
        self.assertEqual(w.state["primaryId"], "main")
        self.assertEqual(w.state["secondaryId"], "")
        self.assertFalse(w.state["pipAvailable"])

    def test_missing_stream_remains_unavailable(self):
        w = StreamWorkspace(MissingStream())
        w.autoSelect()
        self.assertEqual(w.state["primaryId"], "")
        self.assertEqual(w.state["secondaryId"], "")
        self.assertFalse(w.state["pipAvailable"])

    def test_cannot_select_unknown_or_same_secondary(self):
        w = StreamWorkspace(Devices())
        w.autoSelect()
        self.assertFalse(w.selectPrimary("missing"))
        self.assertFalse(w.selectSecondary("main"))

    def test_swap_uses_existing_streams_only(self):
        d = Devices()
        w = StreamWorkspace(d)
        w.autoSelect()
        before = {s['id'] for s in d.activeStreams}
        w.swap()
        self.assertEqual(w.state["primaryId"], "sub")
        self.assertEqual(w.state["secondaryId"], "main")
        self.assertIn(w.state["primaryId"], before)
        self.assertIn(w.state["secondaryId"], before)

    def test_reconcile_preserves_valid_user_selection(self):
        d = Devices()
        w = StreamWorkspace(d)
        w.autoSelect()
        self.assertTrue(w.selectPrimary("thermal"))
        self.assertTrue(w.selectSecondary("main"))
        w.autoSelect()
        self.assertEqual(w.state["primaryId"], "thermal")
        self.assertEqual(w.state["secondaryId"], "main")

    def test_deleted_primary_falls_back_without_reusing_secondary(self):
        d = Devices()
        w = StreamWorkspace(d)
        w.autoSelect()
        w.selectPrimary("thermal")
        w.selectSecondary("sub")
        d.activeStreams = [s for s in d.activeStreams if s["id"] != "thermal"]
        w.autoSelect()
        self.assertEqual(w.state["primaryId"], "main")
        self.assertEqual(w.state["secondaryId"], "sub")

    def test_disabled_secondary_is_replaced_by_real_candidate(self):
        d = Devices()
        w = StreamWorkspace(d)
        w.autoSelect()
        d.activeStreams[1]["enabled"] = False
        w.autoSelect()
        self.assertEqual(w.state["primaryId"], "main")
        self.assertEqual(w.state["secondaryId"], "thermal")
        self.assertTrue(w.state["pipAvailable"])

    def test_primary_takeover_selects_another_real_secondary(self):
        d = Devices()
        w = StreamWorkspace(d)
        w.autoSelect()
        self.assertTrue(w.selectPrimary("sub"))
        self.assertEqual(w.state["primaryId"], "sub")
        self.assertEqual(w.state["secondaryId"], "thermal")


if __name__ == "__main__":
    unittest.main()
