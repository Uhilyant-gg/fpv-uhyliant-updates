"""Fail-closed Queue v3 bridge to privileged merge authorization.

A green Queue v3 decision still waits for the existing merge authority. This bridge
binds that wait state to fresh PR/check/review evidence; it never performs a merge.
"""
from __future__ import annotations

from orchestrator_privileged_merge import MergeAuthorization, authorize
from orchestrator_queue_v3_runner import QueueAction, QueueDecision
from orchestrator_state import PersistedState


def authorize_queue_merge(
    *,
    queue_decision: QueueDecision,
    persisted: PersistedState,
    pr: dict,
    checks: list[dict],
    reviews: list[dict],
    required_checks: set[str],
    security_checks: set[str],
    protected_change: bool,
    security_review_for_head: bool,
) -> MergeAuthorization:
    """Delegate merge authority only from Queue v3's exact green waiting state."""
    persisted.validate()
    if queue_decision.action != QueueAction.WAIT:
        raise ValueError("queue-merge-wait-required")
    if queue_decision.reason_code != "awaiting-existing-merge-gate":
        raise ValueError("queue-merge-gate-reason-required")
    return authorize(
        binding=persisted.binding,
        pr=pr,
        checks=checks,
        reviews=reviews,
        required_checks=required_checks,
        security_checks=security_checks,
        story_id=persisted.story_id,
        protected_change=protected_change,
        security_review_for_head=security_review_for_head,
    )
