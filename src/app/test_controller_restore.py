import unittest
from controller_restore import controller_restore


MAPPING = {
    'roll': {'channel': 0, 'reversed': False},
    'pitch': {'channel': 1, 'reversed': False},
    'yaw': {'channel': 2, 'reversed': False},
    'throttle': {'channel': 3, 'reversed': False},
}
PROFILE = {
    'schemaVersion': 1,
    'controllerId': 'x',
    'channelCount': 4,
    'calibration': [
        {'minimum': 1000, 'center': 1500, 'maximum': 2000},
        {'minimum': 1000, 'center': 1500, 'maximum': 2000},
        {'minimum': 1000, 'center': 1500, 'maximum': 2000},
        {'minimum': 1000, 'center': 1500, 'maximum': 2000},
    ],
    'mapping': MAPPING,
}


def test_saved_record_is_not_presence(): assert controller_restore({'id':'x'},None)['restored'] is False
def test_identity_must_match(): assert controller_restore({'id':'x'},{'id':'y','connected':True,'channels':[1]})['health']=='unknown'
def test_restore_requires_observed_input(): assert controller_restore({'id':'x'},{'id':'x','connected':True})['restored'] is False
def test_invalid_observed_input_does_not_restore():
 r=controller_restore({'id':'x','profile':PROFILE},{'id':'x','connected':True,'channels':[1500,None,1500,1500]})
 assert r['restored'] is False and r['health']=='problem'
def test_fresh_match_with_valid_inputs_restores():
 r=controller_restore({'id':'x','profile':PROFILE},{'id':'x','connected':True,'channels':[1500,1500,1500,1500]})
 assert r['restored'] is True and r['inputHealth']=='ready' and r['channelCount']==4
 assert r['controls']=={'roll':0.0,'pitch':0.0,'yaw':0.0,'throttle':0.5}

def test_restore_needs_controller_bound_profile():
 r=controller_restore({'id':'x','profile':{**PROFILE,'controllerId':'other'}},{'id':'x','connected':True,'channels':[1500]*4})
 assert r['restored'] is False and r['reasonCode']=='controller-profile-unavailable'


class ControllerRestoreTests(unittest.TestCase):
    """Run the module-level checks under ``python -m unittest`` (used by CI)."""


for _name, _check in list(globals().items()):
    if _name.startswith('test_') and callable(_check):
        setattr(ControllerRestoreTests, _name, lambda self, _check=_check: _check())


if __name__ == '__main__':
    unittest.main()
