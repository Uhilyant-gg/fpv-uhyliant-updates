"""Compose fail-closed startup restore planning with zero-config readiness."""
from __future__ import annotations
from typing import Any, Mapping

from startup_restore import startup_restore_plan
from zero_config_readiness import zero_config_readiness


def zero_config_startup(
    saved: Mapping[str, Any] | None,
    discovered: Mapping[str, Any] | None,
    camera: Mapping[str, Any] | None,
    workspace: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return deterministic startup state without inventing device or stream evidence."""
    restore = startup_restore_plan(saved, discovered)
    readiness = zero_config_readiness(camera, workspace)
    if readiness.get("health") == "ready" and restore.get("action") != "revalidate-camera":
        return {"health": "ready", "stage": "operate", "action": readiness.get("action"), "reasonCode": readiness.get("reasonCode"), "restore": restore}
    if restore.get("action") in {"revalidate-camera", "connect-camera"}:
        return {"health": readiness.get("health", "unknown") if restore.get("action") == "connect-camera" else "unknown", "stage": restore["stage"], "action": restore["action"], "reasonCode": restore["reasonCode"], "restore": restore}
    return {"health": readiness.get("health", "unknown"), "stage": readiness.get("stage", "discover"), "action": readiness.get("action") or "find-camera", "reasonCode": readiness.get("reasonCode") or "startup-evidence-unavailable", "restore": restore}
