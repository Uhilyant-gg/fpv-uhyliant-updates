from startup_selection import select_startup_camera

def test_requires_explicit_openipc_evidence():
    r=select_startup_camera([{'host':'192.168.1.2','verified':True,'evidence':['onvif']}])
    assert r['health']=='unknown' and r['selected'] is None

def test_single_verified_candidate_preserves_evidence():
    r=select_startup_camera([{'host':'192.168.1.2','verified':True,'evidence':['reachable-service','camera-candidate','verified-openipc']}])
    assert r['health']=='ready' and 'verified-openipc' in r['selected']['evidence']

def test_ambiguity_fails_closed():
    items=[{'host':f'192.168.1.{n}','verified':True,'evidence':['verified-openipc']} for n in (2,3)]
    assert select_startup_camera(items)['reasonCode']=='camera-selection-ambiguous'
