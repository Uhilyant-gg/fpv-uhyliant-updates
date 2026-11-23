from controller_restore import controller_restore


def test_saved_record_is_not_presence(): assert controller_restore({'id':'x'},None)['restored'] is False
def test_identity_must_match(): assert controller_restore({'id':'x'},{'id':'y','connected':True,'channels':[1]})['health']=='unknown'
def test_restore_requires_observed_input(): assert controller_restore({'id':'x'},{'id':'x','connected':True})['restored'] is False
def test_invalid_observed_input_does_not_restore():
 r=controller_restore({'id':'x'},{'id':'x','connected':True,'channels':[1500,None]})
 assert r['restored'] is False and r['health']=='problem'
def test_fresh_match_with_valid_inputs_restores():
 r=controller_restore({'id':'x'},{'id':'x','connected':True,'channels':[0.2,0.4]})
 assert r['restored'] is True and r['inputHealth']=='ready' and r['channelCount']==2
