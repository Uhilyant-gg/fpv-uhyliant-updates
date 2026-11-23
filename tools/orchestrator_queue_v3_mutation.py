"""Final fail-closed gate before autonomous repair branch mutation.

This module validates that an already-approved patch application plan still targets
the exact observed repair branch HEAD. It returns mutation data but performs no write.
"""
from __future__ import annotations

from dataclasses import dataclass

from orchestrator_queue_v3_patch import PatchApplicationPlan
from orchestrator_v2 import State


@dataclass(frozen=True)
class MutationPlan:
    branch: str
    expected_head_sha: str
    files: tuple[tuple[str, str], ...]
    next_state: State


def prepare_mutation(
    *,
    plan: PatchApplicationPlan,
    branch: str,
    observed_head_sha: str,
) -> MutationPlan:
    branch = branch.strip()
    observed_head_sha = observed_head_sha.strip()
    if not branch:
        raise ValueError("mutation-branch-required")
    if branch in {"main", "master"}:
        raise ValueError("mutation-direct-main-blocked")
    if not observed_head_sha:
        raise ValueError("mutation-observed-head-required")
    if observed_head_sha != plan.expected_head_sha:
        raise ValueError("mutation-stale-head")
    if plan.next_state != State.CI_RUNNING:
        raise ValueError("mutation-ci-rerun-required")
    return MutationPlan(
        branch,
        observed_head_sha,
        tuple((item.path, item.content) for item in plan.files),
        State.CI_RUNNING,
    )
