import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_bootstrap import find_compatible_python, preflight


class ProjectBootstrapTests(unittest.TestCase):
    def test_python_version_policy_is_explicit(self):
        executable, detail = find_compatible_python()
        if executable is not None:
            self.assertIsInstance(executable, Path)
            self.assertIn(".", detail)
        else:
            self.assertIn("3.10-3.13", detail)

    def test_preflight_reports_missing_canonical_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = preflight(root)
            self.assertFalse(result["ok"])
            canonical = next(check for check in result["checks"] if check["name"] == "canonical-files")
            self.assertFalse(canonical["ok"])

    @patch("project_bootstrap.find_compatible_python", return_value=(Path("python"), "3.11"))
    def test_preflight_accepts_minimum_workspace_shape(self, _finder):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / ".git").write_text("gitdir", encoding="utf-8")
            (root / "src" / "requirements.txt").write_text("", encoding="utf-8")
            (root / "src" / "launcher.py").write_text("", encoding="utf-8")
            for name in (
                "PRODUCT_UX.md",
                "PROJECT_STATE.md",
                "PROJECT_STATE.json",
                "DELIVERY_ROADMAP.md",
                "DEVELOPMENT_GUIDE.md",
            ):
                (root / name).write_text("", encoding="utf-8")
            result = preflight(root)
            self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
