"""Deterministic Next Best Action selection over canonical health evidence.

The selector only chooses actions explicitly exposed by component safeActions.
It never upgrades health, invents evidence, or authorizes an operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

HEALTH_PRIORITY = {
    "problem": 0,
    "unknown": 1,
    "attention": 2,
    "ready": 3,
}

ACTION_PRIORITY = {
    "diagnose": 0,
    "find-camera": 10,
    "identify-camera": 20,
    "refresh-identity": 30,
    "verify-camera": 40,
    "show-video": 50,
}


@dataclass(frozen=True)
class NextBestAction:
    action: str | None
    reasonCode: str
    source: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"action": self.action, "reasonCode": self.reasonCode, "source": self.source}


def _candidates(health_by_component: Mapping[str, Mapping[str, Any]]) -> Iterable[tuple[int, int, str, str]]:
    for source, health in health_by_component.items():
        if not isinstance(health, Mapping):
            continue
        health_rank = HEALTH_PRIORITY.get(health.get("health"), HEALTH_PRIORITY["unknown"])
        actions = health.get("safeActions", ())
        if not isinstance(actions, (list, tuple)):
            continue
        for action in actions:
            if action in ACTION_PRIORITY:
                yield (health_rank, ACTION_PRIORITY[action], source, action)


def select_next_best_action(health_by_component: Mapping[str, Mapping[str, Any]] | None) -> NextBestAction:
    """Return at most one deterministic action already authorized as safe by evidence producers."""
    if not isinstance(health_by_component, Mapping) or not health_by_component:
        return NextBestAction(None, "health-evidence-unavailable")

    candidates = sorted(_candidates(health_by_component))
    if not candidates:
        return NextBestAction(None, "no-safe-action")

    _, _, source, action = candidates[0]
    return NextBestAction(action, "safe-action-selected", source)
