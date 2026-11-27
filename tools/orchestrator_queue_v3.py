"""Deterministic, fail-closed Queue v3 planning primitives.

Queue v3 stores future work as intents only. Exactly one item may be active, and a
post-merge refresh must rebase the remaining queue on the observed merge commit.
The queue never authorizes merge, hardware verification, secrets, or product choices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

BLOCKER_STATUSES = frozenset(
    {
        "PHYSICAL_ACTION_REQUIRED",
        "SECRET_REQUIRED",
        "PRODUCT_DECISION_REQUIRED",
        "AUTOMATION_BLOCKED",
    }
)


@dataclass(frozen=True)
class QueueItem:
    story_id: str
    objective: str

    def validate(self) -> None:
        if not self.story_id.strip():
            raise ValueError("queue-story-required")
        if not self.objective.strip():
            raise ValueError("queue-objective-required")


@dataclass(frozen=True)
class QueuePlan:
    baseline_sha: str
    active: QueueItem
    pending: tuple[QueueItem, ...]

    def validate(self) -> None:
        if not self.baseline_sha.strip():
            raise ValueError("queue-baseline-required")
        self.active.validate()
        for item in self.pending:
            item.validate()
        ids = (self.active.story_id,) + tuple(item.story_id for item in self.pending)
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate-queue-story")


def build_queue(*, baseline_sha: str, items: Iterable[QueueItem]) -> QueuePlan:
    items = tuple(items)
    if not items:
        raise ValueError("queue-empty")
    plan = QueuePlan(baseline_sha.strip(), items[0], items[1:])
    plan.validate()
    return plan


def refresh_after_merge(
    plan: QueuePlan,
    *,
    completed_story_id: str,
    merge_commit_sha: str,
    refreshed_items: Iterable[QueueItem],
) -> QueuePlan | None:
    """Create the next queue from fresh planning output after an exact completion.

    The caller must obtain refreshed_items from current post-merge project state.
    Old pending items are deliberately not promoted automatically.
    """
    plan.validate()
    if completed_story_id != plan.active.story_id:
        raise ValueError("completed-story-not-active")
    if not merge_commit_sha.strip():
        raise ValueError("merge-commit-required")
    refreshed_items = tuple(refreshed_items)
    if not refreshed_items:
        return None
    return build_queue(baseline_sha=merge_commit_sha, items=refreshed_items)


def can_continue(*, blocker_status: str | None) -> bool:
    """Continue only when no explicit blocker is present."""
    if blocker_status is None:
        return True
    if blocker_status in BLOCKER_STATUSES:
        return False
    raise ValueError("unknown-queue-blocker")
