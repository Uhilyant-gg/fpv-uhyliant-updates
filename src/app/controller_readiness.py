"""Evidence-only readiness for future controller onboarding."""
from __future__ import annotations
from typing import Any, Mapping


def controller_readiness(observed: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(observed, Mapping):
        return {"health":"unknown","action":"connect-controller","reasonCode":"controller-evidence-unavailable"}
    if observed.get("connected") is not True:
        return {"health":"unknown","action":"connect-controller","reasonCode":"controller-not-confirmed"}
    channels=observed.get("channels")
    if not isinstance(channels,(list,tuple)) or not channels:
        return {"health":"unknown","action":"diagnose","reasonCode":"controller-input-unavailable"}
    if observed.get("calibrated") is not True:
        return {"health":"attention","action":"calibrate-controller","reasonCode":"controller-calibration-required"}
    if observed.get("mappingValid") is not True:
        return {"health":"attention","action":None,"reasonCode":"controller-mapping-required"}
    return {"health":"ready","action":None,"reasonCode":"controller-ready"}
