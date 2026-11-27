from diagnostic_remediation_loop import diagnostic_remediation_loop

def test_destructive_is_service_mode(): assert diagnostic_remediation_loop({'remediationKind':'fullflash'},True,{'state':'ready'})['reasonCode']=='service-mode-required'
def test_execution_without_revalidation_unknown(): assert diagnostic_remediation_loop({'state':'problem','remediationKind':'non-destructive'},True,None)['health']=='unknown'
def test_unchanged_finding_not_ready(): assert diagnostic_remediation_loop({'state':'problem','remediationKind':'non-destructive'},True,{'state':'problem','fresh':True})['health']=='attention'
def test_ready_only_after_revalidation(): assert diagnostic_remediation_loop({'state':'problem','remediationKind':'non-destructive'},True,{'state':'ready','fresh':True})['health']=='ready'
def test_stale_revalidation_is_not_ready(): assert diagnostic_remediation_loop({'state':'problem','remediationKind':'non-destructive'},True,{'state':'ready'})['health']=='unknown'


def load_tests(loader, tests, pattern):
    """Expose this module's pytest-style test functions to unittest (CI and Project Doctor)."""
    import inspect
    import unittest

    suite = unittest.TestSuite(tests)
    for name, function in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(function) and function.__module__ == __name__:
            suite.addTest(unittest.FunctionTestCase(function, description=f"{__name__}.{name}"))
    return suite
