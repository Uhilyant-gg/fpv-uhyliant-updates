import hashlib,tempfile,unittest
from pathlib import Path
from updater_install import helper_args, install_decision, stage_ready_package


class Tests(unittest.TestCase):
    def test_install_decision_is_fail_closed(self):
        self.assertEqual(install_decision(True, True, True), 'busy')
        self.assertEqual(install_decision(False, False, True), 'blocked')
        self.assertEqual(install_decision(False, True, False), 'unavailable')
        self.assertEqual(install_decision(False, True, True), 'handoff')

    def test_stages_verified_package_directly_under_install_root_updates(self):
        with tempfile.TemporaryDirectory() as data, tempfile.TemporaryDirectory() as root:
            source=Path(data)/'package.zip';source.write_bytes(b'package');digest=hashlib.sha256(b'package').hexdigest()
            staged=stage_ready_package(root,{'version':'2.0.12','package':str(source),'sha256':digest})
            target=Path(staged['package']);self.assertEqual(target.parent,Path(root).resolve()/'updates');self.assertEqual(target.read_bytes(),b'package');self.assertEqual(staged['sha256'],digest)

    def test_staging_rejects_changed_package(self):
        with tempfile.TemporaryDirectory() as data, tempfile.TemporaryDirectory() as root:
            source=Path(data)/'package.zip';source.write_bytes(b'changed')
            with self.assertRaises(RuntimeError):stage_ready_package(root,{'version':'2.0.12','package':str(source),'sha256':'a'*64})

    def test_helper_args_bind_verified_ready_identity(self):
        ready = {'version':'2.0.12','package':'C:/FPV/updates/package.zip','sha256':'a'*64}
        args = helper_args(Path('C:/FPV/FPV-Uhyliant-Update.exe'), Path('C:/FPV'), ready, 42)
        self.assertEqual(args[1:3], ['--root', 'C:/FPV'])
        self.assertEqual(args[3:5], ['--package', ready['package']])
        self.assertEqual(args[5:7], ['--version', ready['version']])
        self.assertEqual(args[7:9], ['--sha256', ready['sha256']])
        self.assertEqual(args[9:11], ['--wait-pid', '42'])

    def test_helper_args_reject_extra_ready_fields_and_bad_pid(self):
        ready = {'version':'2.0.12','package':'package.zip','sha256':'a'*64,'extra':True}
        with self.assertRaises(RuntimeError): helper_args('helper.exe', 'root', ready, 42)
        ready.pop('extra')
        for pid in (0, -1, True):
            with self.assertRaises(RuntimeError): helper_args('helper.exe', 'root', ready, pid)


if __name__ == '__main__':
    unittest.main()
