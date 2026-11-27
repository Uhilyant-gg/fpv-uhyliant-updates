"""Vehicle runtime to unified health presentation adapter."""

from typing import Any, Mapping

from unified_health import HEALTH_ATTENTION, HEALTH_PROBLEM, HEALTH_READY, health_evidence, unknown_health


def vehicle_health(snapshot: Mapping[str, Any] | None, diagnostics: Mapping[str, Any] | None):
    if not isinstance(snapshot, Mapping) or not snapshot:
        return unknown_health(
            state="missing", summary="Vehicle evidence is unavailable.", reason_code="vehicle-evidence-missing"
        )

    telemetry = snapshot.get("telemetry")
    video = snapshot.get("video")
    if not isinstance(telemetry, Mapping):
        telemetry = {}
    if not isinstance(video, Mapping):
        video = {}
    diagnostics = diagnostics if isinstance(diagnostics, Mapping) else {}
    issues = diagnostics.get("issues")
    if not isinstance(issues, list):
        issues = []
    if any(isinstance(item, Mapping) and item.get("severity") == "error" for item in issues):
        return health_evidence(
            state="fault",
            health=HEALTH_PROBLEM,
            summary="Vehicle operation has a reported problem.",
            reason_code="vehicle-runtime-problem",
            evidence={"telemetryConnected": telemetry.get("connected"), "videoState": video.get("state")},
            safe_actions=("diagnose",),
        )

    connected = telemetry.get("connected")
    video_state = video.get("state")
    if connected is not True:
        return unknown_health(
            state="telemetry-unknown",
            summary="Current vehicle telemetry is not confirmed.",
            reason_code="telemetry-not-confirmed",
            evidence={"telemetryConnected": connected, "videoState": video_state},
            safe_actions=("diagnose",),
        )
    if video_state in (None, "", "idle", "unknown"):
        return unknown_health(
            state="video-unknown",
            summary="Current video state is not confirmed.",
            reason_code="video-state-unknown",
            evidence={"telemetryConnected": True, "videoState": video_state},
            safe_actions=("show-video",) if video_state == "idle" else (),
        )
    if video_state in ("stalled", "reconnecting"):
        return health_evidence(
            state=str(video_state),
            health=HEALTH_ATTENTION,
            summary="Video needs attention while telemetry remains confirmed.",
            reason_code="video-attention",
            evidence={"telemetryConnected": True, "videoState": video_state},
            safe_actions=("diagnose",),
        )
    if video_state == "error":
        return health_evidence(
            state="video-error",
            health=HEALTH_PROBLEM,
            summary="Video is unavailable because of a reported error.",
            reason_code="video-problem",
            evidence={"telemetryConnected": True, "videoState": "error"},
            safe_actions=("diagnose",),
        )
    if video_state not in ("playing", "connected", "ready"):
        return unknown_health(
            state="video-unmapped",
            summary="Video state has no verified health mapping.",
            reason_code="video-state-unmapped",
            evidence={"telemetryConnected": True, "videoState": video_state},
        )
    return health_evidence(
        state="operational",
        health=HEALTH_READY,
        summary="Vehicle telemetry and video are currently available.",
        reason_code="vehicle-runtime-ready",
        evidence={"telemetryConnected": True, "videoState": video_state},
    )
