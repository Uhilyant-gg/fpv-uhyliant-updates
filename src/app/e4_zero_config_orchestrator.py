"""Evidence-gated composition for the normal zero-config startup journey."""
from typing import Any, Mapping


def e4_zero_config_orchestrator(e: Mapping[str, Any] | None) -> dict[str, Any]:
    e = e if isinstance(e, Mapping) else {}
    restore = e.get("restore") if isinstance(e.get("restore"), Mapping) else {}
    discovery = e.get("discovery") if isinstance(e.get("discovery"), Mapping) else {}
    camera = e.get("camera") if isinstance(e.get("camera"), Mapping) else {}
    video = e.get("video") if isinstance(e.get("video"), Mapping) else {}

    restored = restore.get("restored") is True
    discovered = discovery.get("complete") is True
    if not restored and not discovered:
        return {"health": "unknown", "stage": "discover", "action": "find-camera", "reasonCode": "discovery-evidence-required"}
    if restored and not discovered and restore.get("fresh") is not True:
        return {"health": "unknown", "stage": "discover", "action": "find-camera", "reasonCode": "restored-camera-revalidation-required"}
    if discovery.get("ambiguous") is True:
        return {"health": "attention", "stage": "discover", "action": None, "reasonCode": "camera-selection-ambiguous"}
    if camera.get("verified") is not True or camera.get("usable") is not True:
        return {"health": "unknown", "stage": "camera", "action": "verify-camera", "reasonCode": "verified-usable-camera-required"}
    if video.get("prepared") is not True:
        return {"health": "attention", "stage": "video", "action": "show-video", "reasonCode": "video-preparation-required"}
    if video.get("freshPlayback") is not True:
        return {"health": "attention", "stage": "video", "action": "reconnect-video", "reasonCode": "fresh-playback-required"}
    if video.get("health") != "ready":
        return {"health": "attention", "stage": "video", "action": "diagnose", "reasonCode": "runtime-health-required"}
    return {"health": "ready", "stage": "operate", "action": None, "reasonCode": "zero-config-operational"}
