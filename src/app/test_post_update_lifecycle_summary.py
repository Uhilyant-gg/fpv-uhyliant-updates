from post_update_lifecycle_summary import post_update_lifecycle_summary

def test_sysupgrade_alone_is_not_success(): assert post_update_lifecycle_summary({'sysupgradeComplete':True})['health']=='unknown'
def test_observed_firmware_required():
 r=post_update_lifecycle_summary({'rediscovered':True,'verifiedOpenIPC':True,'platformMatch':True,'sensorMatch':True})
 assert 'observedFirmware' in r['missing']
def test_software_contract_never_claims_physical_evidence():
 r=post_update_lifecycle_summary({'rediscovered':True,'verifiedOpenIPC':True,'platformMatch':True,'sensorMatch':True,'observedFirmware':'v1'})
 assert r['health']=='ready' and r['physicalEvidence'] is False


def load_tests(loader, tests, pattern):
    """Expose this module's pytest-style test functions to unittest (CI and Project Doctor)."""
    import inspect
    import unittest

    suite = unittest.TestSuite(tests)
    for name, function in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(function) and function.__module__ == __name__:
            suite.addTest(unittest.FunctionTestCase(function, description=f"{__name__}.{name}"))
    return suite
