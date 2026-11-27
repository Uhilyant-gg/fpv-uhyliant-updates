"""Evidence-only readiness for future controller onboarding."""

from __future__ import annotations
from typing import Any, Mapping
from controller_input_health import controller_input_health


def controller_readiness(observed: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(observed, Mapping):
        return {"health": "unknown", "action": "connect-controller", "reasonCode": "controller-evidence-unavailable"}
    if observed.get("connected") is not True:
        return {"health": "unknown", "action": "connect-controller", "reasonCode": "controller-not-confirmed"}
    inputs = controller_input_health(observed)
    if inputs["health"] == "unknown":
        return {"health": "unknown", "action": "diagnose", "reasonCode": inputs["reasonCode"]}
    if inputs["health"] == "problem":
        return {"health": "problem", "action": "diagnose", "reasonCode": inputs["reasonCode"]}
    if observed.get("calibrated") is not True:
        return {
            "health": "attention",
            "action": "calibrate-controller",
            "reasonCode": "controller-calibration-required",
        }
    if observed.get("mappingValid") is not True:
        return {"health": "attention", "action": "map-controller-inputs", "reasonCode": "controller-mapping-required"}
    return {"health": "ready", "action": None, "reasonCode": "controller-ready"}
