"""Practical, bounded presentation for diagnostic findings."""

from __future__ import annotations
from typing import Any, Mapping


def diagnostic_finding(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {
            "state": "unknown",
            "summary": "Стан потребує діагностики.",
            "reasonCode": "diagnostic-evidence-unavailable",
            "safeAction": "diagnose",
        }
    state = value.get("health") if value.get("health") in {"ready", "attention", "problem", "unknown"} else "unknown"
    summary = (
        value.get("summary")
        if isinstance(value.get("summary"), str) and value.get("summary")
        else "Стан потребує діагностики."
    )
    reason = (
        value.get("reasonCode")
        if isinstance(value.get("reasonCode"), str) and value.get("reasonCode")
        else "diagnostic-evidence-unavailable"
    )
    actions = value.get("safeActions") if isinstance(value.get("safeActions"), (list, tuple)) else ()
    safe_action = "diagnose" if "diagnose" in actions else None
    return {"state": state, "summary": summary, "reasonCode": reason, "safeAction": safe_action}
