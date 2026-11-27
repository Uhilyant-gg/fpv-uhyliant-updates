"""Unified user-facing health and evidence contract.

This module is intentionally pure and conservative: unknown evidence remains unknown,
and safe actions must be supplied explicitly by the subsystem producing the evidence.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

HEALTH_READY = "ready"
HEALTH_ATTENTION = "attention"
HEALTH_PROBLEM = "problem"
HEALTH_UNKNOWN = "unknown"
HEALTH_VALUES = frozenset({HEALTH_READY, HEALTH_ATTENTION, HEALTH_PROBLEM, HEALTH_UNKNOWN})
SAFE_ACTION_VALUES = frozenset(
    {
        "connect-camera",
        "diagnose",
        "find-camera",
        "identify-camera",
        "refresh-identity",
        "review-firmware",
        "show-video",
        "verify-camera",
    }
)


@dataclass(frozen=True)
class HealthEvidence:
    state: str
    health: str
    summary: str
    reasonCode: str
    evidence: Mapping[str, Any] = field(default_factory=dict)
    safeActions: tuple[str, ...] = ()

    def __post_init__(self):
        if self.health not in HEALTH_VALUES:
            raise ValueError(f"invalid-health:{self.health}")
        if not isinstance(self.state, str) or not self.state.strip():
            raise ValueError("state-required")
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise ValueError("summary-required")
        if not isinstance(self.reasonCode, str) or not self.reasonCode.strip():
            raise ValueError("reason-code-required")
        if not isinstance(self.evidence, Mapping):
            raise ValueError("evidence-must-be-mapping")
        if not isinstance(self.safeActions, tuple) or any(
            not isinstance(action, str) or not action.strip() for action in self.safeActions
        ):
            raise ValueError("safe-actions-invalid")
        if len(self.safeActions) != len(set(self.safeActions)):
            raise ValueError("safe-actions-duplicate")
        unknown_actions = set(self.safeActions).difference(SAFE_ACTION_VALUES)
        if unknown_actions:
            raise ValueError("safe-action-not-allowed:" + ",".join(sorted(unknown_actions)))

    def as_dict(self):
        return {
            "state": self.state,
            "health": self.health,
            "summary": self.summary,
            "reasonCode": self.reasonCode,
            "evidence": dict(self.evidence),
            "safeActions": list(self.safeActions),
        }


def health_evidence(
    *,
    state: str,
    health: str,
    summary: str,
    reason_code: str,
    evidence: Mapping[str, Any] | None = None,
    safe_actions: Iterable[str] = (),
) -> HealthEvidence:
    return HealthEvidence(
        state=state,
        health=health,
        summary=summary,
        reasonCode=reason_code,
        evidence=dict(evidence or {}),
        safeActions=tuple(safe_actions),
    )


def unknown_health(
    *,
    state: str = "unknown",
    summary: str = "Evidence is insufficient.",
    reason_code: str = "insufficient-evidence",
    evidence: Mapping[str, Any] | None = None,
    safe_actions: Iterable[str] = (),
) -> HealthEvidence:
    return health_evidence(
        state=state,
        health=HEALTH_UNKNOWN,
        summary=summary,
        reason_code=reason_code,
        evidence=evidence,
        safe_actions=safe_actions,
    )


def aggregate_health(
    items: Iterable[HealthEvidence], *, state: str = "aggregate", summary: str = "Combined health."
) -> HealthEvidence:
    items = tuple(items)
    if not items:
        return unknown_health(state=state, summary="No health evidence is available.")

    # Fail closed for presentation: a problem dominates, then unknown, then attention.
    # Ready is emitted only when every input is explicitly ready.
    healths = {item.health for item in items}
    if HEALTH_PROBLEM in healths:
        health = HEALTH_PROBLEM
        reason = "component-problem"
    elif HEALTH_UNKNOWN in healths:
        health = HEALTH_UNKNOWN
        reason = "component-unknown"
    elif HEALTH_ATTENTION in healths:
        health = HEALTH_ATTENTION
        reason = "component-attention"
    elif healths == {HEALTH_READY}:
        health = HEALTH_READY
        reason = "all-components-ready"
    else:
        health = HEALTH_UNKNOWN
        reason = "insufficient-evidence"

    return health_evidence(
        state=state,
        health=health,
        summary=summary,
        reason_code=reason,
        evidence={"components": [item.as_dict() for item in items]},
    )
