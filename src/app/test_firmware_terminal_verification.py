from firmware_terminal_verification import firmware_terminal_verification

def test_stale_evidence_cannot_finish(): assert firmware_terminal_verification({'platform':'a','sensor':'b'},{'platform':'a','sensor':'b','verifiedOpenIPC':True,'firmware':'v2'})['verified'] is False
def test_identity_mismatch_fails_closed(): assert firmware_terminal_verification({'platform':'a','sensor':'b'},{'fresh':True,'verifiedOpenIPC':True,'platform':'a','sensor':'c','firmware':'v2'})['health']=='problem'
def test_missing_observed_firmware_unknown(): assert firmware_terminal_verification({'platform':'a','sensor':'b'},{'fresh':True,'verifiedOpenIPC':True,'platform':'a','sensor':'b'})['health']=='unknown'
def test_complete_software_verification_is_not_physical_evidence():
 r=firmware_terminal_verification({'platform':'a','sensor':'b'},{'fresh':True,'verifiedOpenIPC':True,'platform':'a','sensor':'b','firmware':'v2'})
 assert r['verified'] is True and r['physicalEvidence'] is False


def load_tests(loader, tests, pattern):
    """Expose this module's pytest-style test functions to unittest (CI and Project Doctor)."""
    import inspect
    import unittest

    suite = unittest.TestSuite(tests)
    for name, function in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(function) and function.__module__ == __name__:
            suite.addTest(unittest.FunctionTestCase(function, description=f"{__name__}.{name}"))
    return suite
