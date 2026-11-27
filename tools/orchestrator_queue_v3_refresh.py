"""Fail-closed Queue v3 post-merge refresh bridge.

A completed queue item may advance only from validated merge evidence and fresh
planner output. Old pending work is never promoted implicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from orchestrator_post_merge import MergeEvidence
from orchestrator_queue_v3 import QueueItem, QueuePlan, refresh_after_merge


@dataclass(frozen=True)
class RefreshObservation:
    baseline_sha: str
    merge_evidence: MergeEvidence

    def validate(self) -> None:
        self.merge_evidence.validate()
        if not self.baseline_sha.strip():
            raise ValueError("refresh-observed-baseline-required")
        if self.baseline_sha != self.merge_evidence.merge_commit_sha:
            raise ValueError("refresh-main-not-at-merge-commit")


def refresh_queue_from_merge(
    *,
    plan: QueuePlan,
    completed_story_id: str,
    expected_pr: int,
    expected_head_sha: str,
    observation: RefreshObservation,
    refreshed_items: Iterable[QueueItem],
) -> QueuePlan | None:
    """Rebuild Queue v3 only when merge identity and observed main agree."""
    plan.validate()
    observation.validate()
    evidence = observation.merge_evidence
    if completed_story_id != plan.active.story_id:
        raise ValueError("refresh-completed-story-not-active")
    if evidence.pr != expected_pr:
        raise ValueError("refresh-merged-pr-mismatch")
    if evidence.merged_head_sha != expected_head_sha:
        raise ValueError("refresh-merged-head-mismatch")
    return refresh_after_merge(
        plan,
        completed_story_id=completed_story_id,
        merge_commit_sha=evidence.merge_commit_sha,
        refreshed_items=refreshed_items,
    )
