from device_address_continuity import device_address_continuity

def test_dhcp_change_requires_verified_openipc(): assert device_address_continuity({'host':'10.0.0.2','platform':'gk7205v200','sensor':'imx335'},{'host':'10.0.0.9','platform':'gk7205v200','sensor':'imx335'})['accepted'] is False
def test_matching_identity_accepts_new_address():
 r=device_address_continuity({'host':'10.0.0.2','platform':'gk7205v200','sensor':'imx335'},{'host':'10.0.0.9','platform':'gk7205v200','sensor':'imx335','verifiedOpenIPC':True})
 assert r['accepted'] is True and r['addressChanged'] is True
def test_identity_mismatch_fails_closed(): assert device_address_continuity({'platform':'a','sensor':'b'},{'host':'10.0.0.9','platform':'a','sensor':'c','verifiedOpenIPC':True})['health']=='problem'


def load_tests(loader, tests, pattern):
    """Expose this module's pytest-style test functions to unittest (CI and Project Doctor)."""
    import inspect
    import unittest

    suite = unittest.TestSuite(tests)
    for name, function in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(function) and function.__module__ == __name__:
            suite.addTest(unittest.FunctionTestCase(function, description=f"{__name__}.{name}"))
    return suite
