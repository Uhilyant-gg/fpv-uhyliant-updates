"""Bounded presentation of existing network findings."""
from __future__ import annotations
from typing import Any, Mapping

_ALLOWED = {"ready", "attention", "problem", "unknown"}


def network_health_summary(finding: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(finding, Mapping):
        return {"health": "unknown", "summary": "Стан мережі не підтверджено.", "reasonCode": "network-evidence-unavailable", "safeAction": None}
    health = finding.get("state") if finding.get("state") in _ALLOWED else "unknown"
    summary = finding.get("problem") if isinstance(finding.get("problem"), str) and finding.get("problem") else "Стан мережі не підтверджено."
    action = finding.get("action") if isinstance(finding.get("action"), str) else None
    return {"health": health, "summary": summary, "reasonCode": "network-" + health, "safeAction": action}
