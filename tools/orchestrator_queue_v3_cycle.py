"""Fail-closed bridge between persisted Orchestrator state and Queue v3 decisions.

The bridge converts already-observed lifecycle facts into a Queue v3 decision. It
performs no merge, repair, hardware operation, secret access, or queue promotion.
"""
from __future__ import annotations

from dataclasses import dataclass

from orchestrator_queue_v3 import QueuePlan
from orchestrator_queue_v3_runner import QueueDecision, decide_queue_action
from orchestrator_state import PersistedState


@dataclass(frozen=True)
class QueueObservation:
    baseline_sha: str
    ci_status: str
    merged: bool = False
    blocker_status: str | None = None

    def validate(self) -> None:
        if not self.baseline_sha.strip():
            raise ValueError("cycle-observed-baseline-required")
        if self.ci_status not in {"queued", "running", "failed", "green"}:
            raise ValueError("cycle-unknown-ci-status")


def decide_cycle(*, plan: QueuePlan, persisted: PersistedState, observation: QueueObservation) -> QueueDecision:
    """Bind queue, persisted lifecycle state, and fresh observations before deciding."""
    plan.validate()
    persisted.validate()
    observation.validate()
    if persisted.story_id != plan.active.story_id:
        raise ValueError("cycle-story-binding-mismatch")
    if persisted.baseline_sha != plan.baseline_sha:
        raise ValueError("cycle-persisted-baseline-mismatch")
    return decide_queue_action(
        plan,
        active_story_id=persisted.story_id,
        observed_baseline_sha=observation.baseline_sha,
        ci_status=observation.ci_status,
        merged=observation.merged,
        blocker_status=observation.blocker_status,
        repair_attempts=persisted.repair_attempts,
        max_repair_attempts=persisted.max_repair_attempts,
    )
