"""Read-only summary of the stream workspace selection."""

from __future__ import annotations
from typing import Any, Mapping


def video_workspace_summary(state: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(state, Mapping):
        return {
            "health": "unknown",
            "primaryReady": False,
            "pipReady": False,
            "reasonCode": "video-workspace-unavailable",
        }
    primary = state.get("primaryId")
    secondary = state.get("secondaryId")
    primary_ready = isinstance(primary, str) and bool(primary)
    pip_ready = (
        primary_ready
        and isinstance(secondary, str)
        and bool(secondary)
        and secondary != primary
        and state.get("pipAvailable") is True
    )
    return {
        "health": "ready" if primary_ready else "unknown",
        "primaryReady": primary_ready,
        "pipReady": pip_ready,
        "reasonCode": "video-primary-selected" if primary_ready else "video-primary-unavailable",
    }
