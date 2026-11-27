import unittest
from openipc_ssh_transport import ExistingSshTransport


class Result:
    def __init__(self, code=0):
        self.returncode = code


class Runner:
    def __init__(self, code=0):
        self.calls = []
        self.code = code

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return Result(self.code)


class Tests(unittest.TestCase):
    def test_uses_batch_mode_strict_host_key_and_fixed_command(self):
        r = Runner()
        t = ExistingSshTransport(r)
        self.assertTrue(t.run('192.168.1.50', ['sysupgrade', '-k', '-r']))
        cmd = r.calls[0][0][0]
        self.assertEqual(cmd[-4:], ['root@192.168.1.50', 'sysupgrade', '-k', '-r'])
        self.assertIn('BatchMode=yes', cmd)
        self.assertIn('StrictHostKeyChecking=yes', cmd)

    def test_rejects_command_injection_and_other_commands(self):
        r = Runner()
        t = ExistingSshTransport(r)
        self.assertFalse(t.run('192.168.1.50; reboot', ['sysupgrade', '-k', '-r']))
        self.assertFalse(t.run('192.168.1.50', ['reboot']))
        self.assertEqual(r.calls, [])

    def test_transport_failure_is_fail_closed(self):
        r = Runner(255)
        self.assertFalse(ExistingSshTransport(r).run('192.168.1.50', ['sysupgrade', '-k', '-r']))


if __name__ == '__main__':
    unittest.main()
