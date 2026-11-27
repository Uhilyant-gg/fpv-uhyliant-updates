"""Deterministic, non-destructive startup restore/discovery planning."""

from __future__ import annotations
from typing import Any, Mapping


def startup_restore_plan(saved: Mapping[str, Any] | None, discovered: Mapping[str, Any] | None) -> dict[str, Any]:
    """Choose only evidence-backed startup work; never invent fresh device identity."""
    if isinstance(discovered, Mapping) and discovered.get("verified") is True and discovered.get("host"):
        return {
            "stage": "discover",
            "action": "connect-camera",
            "host": discovered["host"],
            "reasonCode": "verified-discovered-camera",
        }
    if isinstance(saved, Mapping) and saved.get("verified") is True and saved.get("host"):
        return {
            "stage": "restore",
            "action": "revalidate-camera",
            "host": saved["host"],
            "reasonCode": "saved-camera-revalidation-required",
        }
    return {"stage": "discover", "action": "find-camera", "host": None, "reasonCode": "no-verified-camera"}
