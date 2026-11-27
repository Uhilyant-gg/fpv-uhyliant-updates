from video_recovery_contract import video_recovery_contract


def test_changed_input_invalidates_prepared():
    assert (
        video_recovery_contract(
            {'sourceFingerprint': 'a'}, {'sourceFingerprint': 'b', 'state': 'playing', 'freshPlayback': True}
        )['prepared']
        is False
    )


def test_stalled_requests_reconnect():
    assert (
        video_recovery_contract({'sourceFingerprint': 'a'}, {'sourceFingerprint': 'a', 'state': 'stalled'})['action']
        == 'reconnect-video'
    )


def test_reconnect_does_not_prove_success():
    assert (
        video_recovery_contract({'sourceFingerprint': 'a'}, {'sourceFingerprint': 'a', 'state': 'ready'})['health']
        == 'attention'
    )


def test_fresh_playback_is_ready():
    assert (
        video_recovery_contract(
            {'sourceFingerprint': 'a'}, {'sourceFingerprint': 'a', 'state': 'playing', 'freshPlayback': True}
        )['health']
        == 'ready'
    )
