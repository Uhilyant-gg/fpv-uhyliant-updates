"""Rebind Queue v3 repair state to the newly mutated HEAD before CI evaluation.

A successful mutation changes the repair branch HEAD. This creates the next persisted
binding only from a validated mutation outcome and never changes the baseline story.
"""

from __future__ import annotations

from dataclasses import replace

from orchestrator_queue_v3_mutation_receipt import MutationOutcome
from orchestrator_state import PersistedState
from orchestrator_v2 import State


def rebind_after_mutation(*, persisted: PersistedState, outcome: MutationOutcome) -> PersistedState:
    persisted.validate()
    if persisted.state != State.REPAIRING:
        raise ValueError("ci-rebind-repair-state-required")
    if outcome.next_state != State.CI_RUNNING:
        raise ValueError("ci-rebind-running-state-required")
    if not outcome.new_head_sha.strip():
        raise ValueError("ci-rebind-head-required")
    if outcome.new_head_sha == persisted.expected_head_sha:
        raise ValueError("ci-rebind-head-must-change")
    rebound = replace(
        persisted,
        state=State.CI_RUNNING,
        expected_head_sha=outcome.new_head_sha,
        repair_attempts=persisted.repair_attempts + 1,
    )
    rebound.validate()
    return rebound
