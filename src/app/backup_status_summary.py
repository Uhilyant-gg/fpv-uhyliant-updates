"""Read-only backup/restore plan presentation without restore authority."""

from __future__ import annotations
from typing import Any, Mapping


def backup_status_summary(result: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        return {"health": "unknown", "restoreReady": False, "reasonCode": "backup-status-unavailable"}
    manifest = result.get("manifest") if isinstance(result.get("manifest"), Mapping) else {}
    verified = result.get("ready") is True and manifest.get("execution") == "explicit-confirmation-required"
    restored = result.get("ready") is True and manifest.get("restored") is True
    if restored:
        return {"health": "ready", "restoreReady": False, "reasonCode": "backup-restore-complete"}
    if verified:
        return {"health": "attention", "restoreReady": True, "reasonCode": "backup-restore-confirmation-required"}
    return {"health": "unknown", "restoreReady": False, "reasonCode": "backup-restore-unavailable"}
