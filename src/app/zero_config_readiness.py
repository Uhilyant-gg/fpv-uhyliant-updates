"""Pure readiness contract for the zero-config startup journey."""
from __future__ import annotations
from typing import Any, Mapping


def zero_config_readiness(camera: Mapping[str, Any] | None, workspace: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(camera, Mapping):
        return {"health":"unknown","stage":"discover","action":"find-camera","reasonCode":"camera-evidence-unavailable"}
    if camera.get("health") != "ready":
        actions=camera.get("safeActions") if isinstance(camera.get("safeActions"),(list,tuple)) else ()
        action=next((a for a in actions if a in {"find-camera","identify-camera","refresh-identity","verify-camera","connect-camera"}),None)
        return {"health":camera.get("health") if camera.get("health") in {"attention","problem","unknown"} else "unknown","stage":"camera","action":action,"reasonCode":camera.get("reasonCode") or "camera-not-ready"}
    if not isinstance(workspace, Mapping) or not workspace.get("primaryId"):
        return {"health":"attention","stage":"video","action":"show-video","reasonCode":"primary-stream-not-selected"}
    return {"health":"ready","stage":"operate","action":"show-video","reasonCode":"zero-config-ready"}
