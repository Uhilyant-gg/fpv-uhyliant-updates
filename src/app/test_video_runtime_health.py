from video_runtime_health import video_runtime_health


def test_continuity_without_playback_is_unknown():
    assert video_runtime_health({'continuous': True}, {'state': 'prepared'})['health'] == 'unknown'


def test_stall_requires_reconnect():
    assert video_runtime_health({'continuous': True}, {'state': 'stalled'})['action'] == 'reconnect-video'


def test_reconnect_not_success_without_playback():
    assert video_runtime_health({'continuous': True}, {'state': 'reconnecting'})['health'] == 'unknown'


def test_ready_requires_playback_and_continuity():
    assert video_runtime_health({'continuous': True}, {'state': 'playing'})['health'] == 'ready'
