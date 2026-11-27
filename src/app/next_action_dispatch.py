"""Fail-closed dispatch boundary for presentation-only Next Best Actions.

This module maps normal navigation/intents only. It cannot authorize destructive
firmware or service operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

_TARGETS = {
    "diagnose": "diagnostics",
    "find-camera": "devices",
    "review-firmware": "firmware",
    "identify-camera": "devices",
    "refresh-identity": "devices",
    "verify-camera": "devices",
    "show-video": "fpv",
}


@dataclass(frozen=True)
class NextActionIntent:
    accepted: bool
    action: str | None
    target: str | None
    reasonCode: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "action": self.action,
            "target": self.target,
            "reasonCode": self.reasonCode,
        }


def dispatch_intent(next_action: Mapping[str, Any] | None) -> NextActionIntent:
    """Resolve a selected normal action into a UI intent; reject everything else."""
    if not isinstance(next_action, Mapping):
        return NextActionIntent(False, None, None, "next-action-unavailable")

    action = next_action.get("action")
    target = _TARGETS.get(action)
    if target is None:
        return NextActionIntent(False, None, None, "next-action-not-dispatchable")

    if next_action.get("reasonCode") != "safe-action-selected":
        return NextActionIntent(False, None, None, "next-action-not-authorized")

    return NextActionIntent(True, action, target, "next-action-dispatched")
