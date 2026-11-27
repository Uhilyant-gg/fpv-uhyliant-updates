"""Guard: every test_*.py module must expose all of its tests to unittest.

CI and Project Doctor run the suite with ``python -m unittest``, which silently
collects nothing from bare pytest-style ``def test_...()`` functions. A module
that relies on them must define ``load_tests`` (see any adapted module).
"""
import importlib
import inspect
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _ids(item)
        else:
            yield item.shortDescription() if isinstance(item, unittest.FunctionTestCase) else item.id()


class UnittestCollectionTests(unittest.TestCase):
    def test_every_test_function_is_collected_by_unittest(self):
        loader = unittest.TestLoader()
        for path in sorted(HERE.glob("test_*.py")):
            with self.subTest(module=path.stem):
                module = importlib.import_module(path.stem)
                functions = {name for name, value in vars(module).items() if name.startswith("test_") and inspect.isfunction(value) and value.__module__ == module.__name__}
                ids = list(_ids(loader.loadTestsFromModule(module)))
                self.assertTrue(ids, f"{path.name}: unittest collects no tests")
                missing = {name for name in functions if f"{module.__name__}.{name}" not in ids}
                self.assertFalse(missing, f"{path.name}: unittest would skip {sorted(missing)}; add a load_tests adapter")
