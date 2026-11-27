from e4_zero_config_orchestrator import e4_zero_config_orchestrator as run


def test_missing_restore_and_discovery_stays_discover():
    assert run({})["reasonCode"] == "discovery-evidence-required"


def test_stale_restore_requires_fresh_revalidation():
    result = run(
        {
            "restore": {"restored": True},
            "camera": {"verified": True, "usable": True},
            "video": {"prepared": True, "freshPlayback": True, "health": "ready"},
        }
    )
    assert result == {
        "health": "unknown",
        "stage": "discover",
        "action": "find-camera",
        "reasonCode": "restored-camera-revalidation-required",
    }


def test_fresh_restore_can_continue_without_discovery_completion():
    result = run(
        {
            "restore": {"restored": True, "fresh": True},
            "camera": {"verified": True, "usable": True},
            "video": {"prepared": True, "freshPlayback": True, "health": "ready"},
        }
    )
    assert result["stage"] == "operate" and result["health"] == "ready"


def test_completed_discovery_supersedes_stale_restore_hint():
    result = run(
        {
            "restore": {"restored": True},
            "discovery": {"complete": True},
            "camera": {"verified": True, "usable": True},
            "video": {"prepared": True, "freshPlayback": True, "health": "ready"},
        }
    )
    assert result["stage"] == "operate"


def test_ambiguity_is_not_guessed():
    assert run({"discovery": {"complete": True, "ambiguous": True}})["action"] is None


def test_camera_must_be_verified_and_usable():
    assert run({"discovery": {"complete": True}, "camera": {"verified": True}})["stage"] == "camera"


def test_preparation_precedes_playback():
    assert (
        run({"discovery": {"complete": True}, "camera": {"verified": True, "usable": True}})["reasonCode"]
        == "video-preparation-required"
    )


def test_reconnect_does_not_equal_playback():
    assert (
        run(
            {
                "discovery": {"complete": True},
                "camera": {"verified": True, "usable": True},
                "video": {"prepared": True, "health": "ready"},
            }
        )["reasonCode"]
        == "fresh-playback-required"
    )


def test_operate_requires_fresh_ready_video():
    result = run(
        {
            "discovery": {"complete": True},
            "camera": {"verified": True, "usable": True},
            "video": {"prepared": True, "freshPlayback": True, "health": "ready"},
        }
    )
    assert result["stage"] == "operate" and result["health"] == "ready"
