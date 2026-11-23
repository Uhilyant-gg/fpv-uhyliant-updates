"""Deterministic Queue v3 runner decisions.

This layer decides whether the queue waits, repairs, refreshes after merge, or
stops. It never performs merge, invokes hardware, supplies secrets, or promotes
stale pending work.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from orchestrator_queue_v3 import QueuePlan, can_continue


class QueueAction(str, Enum):
    WAIT = "WAIT"
    REPAIR = "REPAIR"
    REFRESH = "REFRESH"
    STOP = "STOP"


@dataclass(frozen=True)
class QueueDecision:
    action: QueueAction
    reason_code: str


def decide_queue_action(
    plan: QueuePlan,
    *,
    active_story_id: str,
    ci_status: str,
    merged: bool = False,
    blocker_status: str | None = None,
    repair_attempts: int = 0,
    max_repair_attempts: int = 3,
) -> QueueDecision:
    plan.validate()
    if active_story_id != plan.active.story_id:
        raise ValueError("runner-active-story-mismatch")
    if repair_attempts < 0 or max_repair_attempts < 0:
        raise ValueError("runner-invalid-repair-budget")
    if not can_continue(blocker_status=blocker_status):
        return QueueDecision(QueueAction.STOP, blocker_status or "queue-blocked")
    if merged:
        if ci_status != "green":
            raise ValueError("runner-merged-without-green-ci")
        return QueueDecision(QueueAction.REFRESH, "post-merge-refresh-required")
    if ci_status in {"queued", "running"}:
        return QueueDecision(QueueAction.WAIT, "ci-in-progress")
    if ci_status == "failed":
        if repair_attempts >= max_repair_attempts:
            return QueueDecision(QueueAction.STOP, "repair-budget-exceeded")
        return QueueDecision(QueueAction.REPAIR, "repair-current-batch")
    if ci_status == "green":
        return QueueDecision(QueueAction.WAIT, "awaiting-existing-merge-gate")
    raise ValueError("runner-unknown-ci-status")
