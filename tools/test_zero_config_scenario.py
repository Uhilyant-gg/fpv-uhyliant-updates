from zero_config_scenario import evaluate_zero_config_scenario


def test_missing_discovery_is_deterministic():
    r = evaluate_zero_config_scenario({})
    assert r['stage'] == 'discovery' and r['reasonCode'] == 'discovery-unavailable'


def test_ambiguity_is_never_guessed():
    r = evaluate_zero_config_scenario({'discovery': True, 'cameraAmbiguous': True})
    assert r['stage'] == 'camera' and r['nextBestAction'] is None


def test_verified_camera_is_required():
    r = evaluate_zero_config_scenario({'discovery': True})
    assert r['reasonCode'] == 'verified-camera-required'


def test_reconnect_is_not_playback_success():
    r = evaluate_zero_config_scenario({'discovery': True, 'verifiedCamera': True, 'videoState': 'ready'})
    assert r['stage'] == 'video' and r['nextBestAction'] == 'reconnect-video'


def test_runtime_health_is_required_after_playback():
    r = evaluate_zero_config_scenario({'discovery': True, 'verifiedCamera': True, 'freshPlayback': True})
    assert r['stage'] == 'operate' and not r['ok']


def test_success_is_software_only():
    r = evaluate_zero_config_scenario(
        {'discovery': True, 'verifiedCamera': True, 'freshPlayback': True, 'runtimeHealthy': True}
    )
    assert r['ok'] is True and r['physicalEvidence'] is False
