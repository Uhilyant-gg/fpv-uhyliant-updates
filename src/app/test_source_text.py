import unittest

from source_text import SourceText


class SourceTextTests(unittest.TestCase):
    def test_containment_ignores_layout_but_not_tokens(self):
        text = SourceText('UPGRADE_ARGV = (\n    "sysupgrade",\n    "-k",\n    "-r",\n)\nx = 1; y = 2\n')
        self.assertIn('UPGRADE_ARGV=("sysupgrade","-k","-r")', text)
        self.assertIn("x=1;y=2", text)
        self.assertNotIn('UPGRADE_ARGV=("sysupgrade","-r")', text)
        self.assertNotIn("x=2", text)

    def test_ordering_uses_consistent_offsets(self):
        text = SourceText("a()\nb()\nc()\n")
        first = text.index("a()")
        self.assertLess(first, text.index("b()", first))
        with self.assertRaises(ValueError):
            text.index("a()", text.index("b()"))


if __name__ == "__main__":
    unittest.main()
