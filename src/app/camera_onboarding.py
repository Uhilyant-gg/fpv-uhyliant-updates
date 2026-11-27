"""Fail-closed readiness policy for adding OpenIPC cameras to the home screen."""
from typing import Any, Mapping

from firmware_center import SUPPORTED_PROFILES


def camera_onboarding(candidate: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(candidate, Mapping):
        return {
            "ready": False,
            "stageable": False,
            "state": "unsupported",
            "reason": "Потрібно підтвердити сумісну камеру OpenIPC.",
            "profile": "",
        }

    identity = candidate.get("identity")
    if not isinstance(identity, Mapping):
        identity = candidate.get("openipcIdentity")
    identity = identity if isinstance(identity, Mapping) else {}
    verified = identity.get("verified") is True and candidate.get("openipc") is not False
    platform = str(identity.get("platform") or "").strip().lower()
    sensor = str(identity.get("sensor") or "").strip().lower()
    profiles = [
        name
        for name, profile in SUPPORTED_PROFILES.items()
        if profile.get("platform") == platform and profile.get("sensor") == sensor
    ]
    profile = profiles[0] if len(profiles) == 1 else ""
    stageable = verified and bool(profile)

    if not verified:
        return {
            "ready": False,
            "stageable": False,
            "state": "unsupported",
            "reason": "OpenIPC ще не підтверджено.",
            "profile": "",
        }
    if not profile:
        return {
            "ready": False,
            "stageable": False,
            "state": "unsupported",
            "reason": "Для цієї платформи та сенсора немає підтвердженого профілю прошивки.",
            "profile": "",
        }

    firmware = str(identity.get("firmware") or "").strip()
    if not firmware:
        return {
            "ready": False,
            "stageable": True,
            "state": "pending-firmware",
            "reason": "Версію прошивки ще не спостережено. Перевірте камеру в Центрі прошивки.",
            "profile": profile,
        }

    streams = candidate.get("streams")
    verified_streams = [
        stream
        for stream in streams if isinstance(stream, Mapping)
        and str(stream.get("protocol", "")).lower() == "rtsp"
        and str(stream.get("path", "")).startswith("/")
        and isinstance(stream.get("port"), int)
        and not isinstance(stream.get("port"), bool)
        and 1 <= stream["port"] <= 65535
    ] if isinstance(streams, (list, tuple)) else []
    if not verified_streams:
        return {
            "ready": False,
            "stageable": True,
            "state": "pending-video",
            "reason": "Прошивку підтверджено, але відеопотік ще не перевірено.",
            "profile": profile,
        }

    return {
        "ready": True,
        "stageable": True,
        "state": "ready",
        "reason": "OpenIPC, апаратний профіль і RTSP-відео підтверджено.",
        "profile": profile,
    }
