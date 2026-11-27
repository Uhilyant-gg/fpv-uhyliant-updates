from video_runtime_health import video_runtime_health

def test_continuity_without_playback_is_unknown(): assert video_runtime_health({'continuous':True},{'state':'prepared'})['health']=='unknown'
def test_stall_requires_reconnect(): assert video_runtime_health({'continuous':True},{'state':'stalled'})['action']=='reconnect-video'
def test_reconnect_not_success_without_playback(): assert video_runtime_health({'continuous':True},{'state':'reconnecting'})['health']=='unknown'
def test_ready_requires_playback_and_continuity(): assert video_runtime_health({'continuous':True},{'state':'playing'})['health']=='ready'


def load_tests(loader, tests, pattern):
    """Expose this module's pytest-style test functions to unittest (CI and Project Doctor)."""
    import inspect
    import unittest

    suite = unittest.TestSuite(tests)
    for name, function in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(function) and function.__module__ == __name__:
            suite.addTest(unittest.FunctionTestCase(function, description=f"{__name__}.{name}"))
    return suite
