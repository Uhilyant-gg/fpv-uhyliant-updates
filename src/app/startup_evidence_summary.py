"""Bounded summary of startup harness evidence."""

from __future__ import annotations
from typing import Any, Mapping


def startup_evidence_summary(latest: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(latest, Mapping):
        return {"health": "unknown", "stage": None, "reasonCode": "startup-evidence-unavailable"}
    stage = latest.get("stage") if isinstance(latest.get("stage"), str) else None
    status = latest.get("status") if isinstance(latest.get("status"), str) else None
    if status == "error":
        health = "problem"
    elif status == "ok" and stage in {"probe-complete", "event-processing-complete"}:
        health = "ready"
    elif status == "ok":
        health = "attention"
    else:
        health = "unknown"
    return {"health": health, "stage": stage, "reasonCode": "startup-" + (status or "unknown")}
