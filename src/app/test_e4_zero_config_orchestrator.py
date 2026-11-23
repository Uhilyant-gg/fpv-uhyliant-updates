from e4_zero_config_orchestrator import e4_zero_config_orchestrator as run

def test_missing_restore_and_discovery_stays_discover(): assert run({})['reasonCode']=='discovery-evidence-required'
def test_ambiguity_is_not_guessed(): assert run({'discovery':{'complete':True,'ambiguous':True}})['action'] is None
def test_camera_must_be_verified_and_usable(): assert run({'discovery':{'complete':True},'camera':{'verified':True}})['stage']=='camera'
def test_preparation_precedes_playback(): assert run({'discovery':{'complete':True},'camera':{'verified':True,'usable':True}})['reasonCode']=='video-preparation-required'
def test_reconnect_does_not_equal_playback(): assert run({'discovery':{'complete':True},'camera':{'verified':True,'usable':True},'video':{'prepared':True,'health':'ready'}})['reasonCode']=='fresh-playback-required'
def test_operate_requires_fresh_ready_video():
 r=run({'discovery':{'complete':True},'camera':{'verified':True,'usable':True},'video':{'prepared':True,'freshPlayback':True,'health':'ready'}});assert r['stage']=='operate' and r['health']=='ready'
