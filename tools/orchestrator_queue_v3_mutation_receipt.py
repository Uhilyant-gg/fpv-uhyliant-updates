"""Verify the repository mutation receipt before Queue v3 returns to CI.

The mutation transport is external. This layer accepts its factual receipt only when
the branch and pre-write HEAD match the approved mutation plan and a new HEAD exists.
"""
from __future__ import annotations

from dataclasses import dataclass

from orchestrator_queue_v3_mutation import MutationPlan
from orchestrator_v2 import State


@dataclass(frozen=True)
class MutationReceipt:
    branch: str
    previous_head_sha: str
    new_head_sha: str

    def validate(self) -> None:
        if not self.branch.strip() or not self.previous_head_sha.strip() or not self.new_head_sha.strip():
            raise ValueError("mutation-receipt-incomplete")
        if self.previous_head_sha == self.new_head_sha:
            raise ValueError("mutation-head-did-not-change")


@dataclass(frozen=True)
class MutationOutcome:
    branch: str
    new_head_sha: str
    next_state: State


def accept_mutation_receipt(*, plan: MutationPlan, receipt: MutationReceipt) -> MutationOutcome:
    receipt.validate()
    if receipt.branch != plan.branch:
        raise ValueError("mutation-receipt-branch-mismatch")
    if receipt.previous_head_sha != plan.expected_head_sha:
        raise ValueError("mutation-receipt-stale-head")
    if plan.next_state != State.CI_RUNNING:
        raise ValueError("mutation-receipt-ci-state-required")
    return MutationOutcome(receipt.branch, receipt.new_head_sha, State.CI_RUNNING)
