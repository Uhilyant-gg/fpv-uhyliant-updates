from video_first_home import video_first_home

def test_video_home_requires_usable_ready_camera(): assert video_first_home({'usable':True,'health':'ready'},None)['home']=='video'
def test_unknown_vocab_is_normalized(): assert video_first_home({'usable':False,'health':'magic'},None)['health']=='unknown'
def test_one_contextual_action_is_exposed(): assert video_first_home(None,{'action':'find-camera'})['nextBestAction']=='find-camera'
def test_presentation_has_no_authority(): assert video_first_home(None,None)['authority']=='presentation-only'


def load_tests(loader, tests, pattern):
    """Expose this module's pytest-style test functions to unittest (CI and Project Doctor)."""
    import inspect
    import unittest

    suite = unittest.TestSuite(tests)
    for name, function in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(function) and function.__module__ == __name__:
            suite.addTest(unittest.FunctionTestCase(function, description=f"{__name__}.{name}"))
    return suite
