"""Conservative device-to-unified-health presentation adapter."""
from typing import Any, Mapping

from unified_health import (
    HEALTH_ATTENTION,
    HEALTH_PROBLEM,
    HEALTH_READY,
    health_evidence,
    unknown_health,
)


def device_health(device: Mapping[str, Any] | None):
    if not device:
        return unknown_health(
            state="missing",
            summary="No device is selected.",
            reason_code="device-not-selected",
            safe_actions=("find-camera",),
        )

    identity = device.get("openipcIdentity")
    if not isinstance(identity, Mapping) or not identity:
        return unknown_health(
            state="identity-unknown",
            summary="Camera identity has not been observed.",
            reason_code="device-identity-unknown",
            evidence={"deviceId": device.get("id"), "host": device.get("host")},
            safe_actions=("identify-camera",),
        )

    if identity.get("verified") is not True:
        return health_evidence(
            state="unverified",
            health=HEALTH_ATTENTION,
            summary="Camera is present but OpenIPC identity is not verified.",
            reason_code="openipc-not-verified",
            evidence={"deviceId": device.get("id"), "verified": identity.get("verified")},
            safe_actions=("verify-camera",),
        )

    platform = identity.get("platform")
    sensor = identity.get("sensor")
    missing = tuple(name for name, value in (("platform", platform), ("sensor", sensor)) if not value)
    if missing:
        return unknown_health(
            state="identity-incomplete",
            summary="Verified OpenIPC camera is missing observed hardware identity.",
            reason_code="hardware-identity-incomplete",
            evidence={"deviceId": device.get("id"), "verified": True, "missing": list(missing)},
            safe_actions=("refresh-identity",),
        )

    connection = device.get("connection")
    if connection == "error":
        return health_evidence(
            state="connection-error",
            health=HEALTH_PROBLEM,
            summary="Camera connection has a reported problem.",
            reason_code="camera-connection-problem",
            evidence={"deviceId": device.get("id"), "connection": "error"},
            safe_actions=("diagnose",),
        )

    # Only an explicit observed disconnect warrants a connect action. Older producers
    # may omit connection entirely; absence must not be reinterpreted as a disconnect.
    if connection == "disconnected":
        return health_evidence(
            state="disconnected",
            health=HEALTH_ATTENTION,
            summary="Verified camera is available but explicitly disconnected.",
            reason_code="camera-connection-needed",
            evidence={"deviceId": device.get("id"), "verified": True, "connection": connection},
            safe_actions=("connect-camera",),
        )

    streams = device.get("streams")
    if isinstance(streams, (list, tuple)) and streams:
        return health_evidence(
            state="verified",
            health=HEALTH_READY,
            summary="Camera identity is verified and a stream is observed.",
            reason_code="camera-video-ready",
            evidence={"deviceId": device.get("id"), "verified": True, "platform": platform, "sensor": sensor},
            safe_actions=("show-video",),
        )

    return health_evidence(
        state="verified",
        health=HEALTH_READY,
        summary="Camera identity is verified and hardware identity is observed.",
        reason_code="camera-identity-ready",
        evidence={"deviceId": device.get("id"), "verified": True, "platform": platform, "sensor": sensor},
    )
