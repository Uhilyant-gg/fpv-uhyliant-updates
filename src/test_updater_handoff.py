import tempfile
import unittest
from pathlib import Path

from updater_handoff import valid_handoff


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.updates = self.root / 'updates'
        self.updates.mkdir()
        self.package = self.updates / 'FPV-Uhyliant-2.0.12.zip'
        self.package.write_bytes(b'package')
        self.digest = 'a' * 64

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_handoff(self):
        self.assertTrue(valid_handoff(self.root, self.package, '2.0.12', self.digest, 123))

    def test_rejects_package_outside_updates_directory(self):
        outside = self.root / 'outside.zip'
        outside.write_bytes(b'package')
        self.assertFalse(valid_handoff(self.root, outside, '2.0.12', self.digest, 123))

    def test_rejects_missing_package(self):
        self.assertFalse(valid_handoff(self.root, self.updates / 'missing.zip', '2.0.12', self.digest, 123))

    def test_rejects_unsafe_or_empty_version(self):
        self.assertFalse(valid_handoff(self.root, self.package, '', self.digest, 123))
        self.assertFalse(valid_handoff(self.root, self.package, '../2.0.12', self.digest, 123))

    def test_rejects_bad_digest(self):
        self.assertFalse(valid_handoff(self.root, self.package, '2.0.12', 'bad', 123))

    def test_rejects_nonpositive_or_boolean_pid(self):
        self.assertFalse(valid_handoff(self.root, self.package, '2.0.12', self.digest, 0))
        self.assertFalse(valid_handoff(self.root, self.package, '2.0.12', self.digest, -1))
        self.assertFalse(valid_handoff(self.root, self.package, '2.0.12', self.digest, True))


if __name__ == '__main__':
    unittest.main()
