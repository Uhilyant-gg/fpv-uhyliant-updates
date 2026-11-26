"""Presentation model for the operational home dashboard."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from device_health import device_health
from next_action_presentation import present_next_action
from next_best_action import select_next_best_action
from station_health import station_health


def _human_state(health: str) -> str:
    return {
        "ready": "Усе готово",
        "attention": "Потрібна увага",
        "problem": "Є проблема",
        "unknown": "Стан перевіряється",
    }.get(health, "Стан перевіряється")


def home_dashboard(
    devices: Iterable[Mapping[str, Any]] | None,
    streams: Iterable[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    items = tuple(device for device in (devices or ()) if isinstance(device, Mapping))
    available_streams = tuple(stream for stream in (streams or ()) if isinstance(stream, Mapping))

    if not items:
        camera = device_health(None)
    else:
        active = next((device for device in items if device.get("active") is True), items[0])
        active_streams = [
            dict(stream)
            for stream in available_streams
            if stream.get("device_id") == active.get("id") and stream.get("enabled") is True
        ]
        camera_data = dict(active)
        camera_data["streams"] = active_streams
        camera = device_health(camera_data)

    combined = station_health([camera])
    next_action = present_next_action(
        select_next_best_action({"camera": camera.as_dict()}).as_dict()
    )

    verified = sum(
        1
        for device in items
        if isinstance(device.get("openipcIdentity"), Mapping)
        and device["openipcIdentity"].get("verified") is True
    )
    warning_count = sum(
        1
        for device in items
        if not isinstance(device.get("openipcIdentity"), Mapping)
        or device["openipcIdentity"].get("verified") is not True
    )

    return {
        "health": combined.health,
        "title": _human_state(combined.health),
        "summary": camera.summary,
        "deviceCount": len(items),
        "verifiedCount": verified,
        "warningCount": warning_count,
        "nextAction": next_action,
    }
