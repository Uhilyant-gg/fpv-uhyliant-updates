"""Deterministic Orchestrator v2 control-plane primitives.

No AI/provider code belongs here. Inputs are evidence gathered by a caller; policy is pure,
small and fail-closed so restart/recovery does not depend on an AI engine.
"""
from dataclasses import dataclass
from enum import Enum


class State(str, Enum):
    READY="READY"; PLANNING="PLANNING"; IMPLEMENTING="IMPLEMENTING"; PR_OPEN="PR_OPEN"
    CI_RUNNING="CI_RUNNING"; CI_FAILED="CI_FAILED"; REPAIRING="REPAIRING"; REVIEWING="REVIEWING"
    READY_TO_MERGE="READY_TO_MERGE"; MERGING="MERGING"; UPDATING_STATE="UPDATING_STATE"
    BLOCKED_HARDWARE="BLOCKED_HARDWARE"; BLOCKED_SECRET="BLOCKED_SECRET"; BLOCKED_PRODUCT="BLOCKED_PRODUCT"
    BLOCKED_AUTOMATION="BLOCKED_AUTOMATION"; STATE_INCONSISTENT="STATE_INCONSISTENT"; COMPLETE="COMPLETE"


FLOW = [State.READY, State.PLANNING, State.IMPLEMENTING, State.PR_OPEN, State.CI_RUNNING,
        State.REVIEWING, State.READY_TO_MERGE, State.MERGING, State.UPDATING_STATE, State.COMPLETE]
_ALLOWED = {s: {FLOW[i+1]} for i, s in enumerate(FLOW[:-1])}
_ALLOWED.update({
    State.CI_RUNNING: {State.CI_FAILED, State.REVIEWING},
    State.CI_FAILED: {State.REPAIRING, State.BLOCKED_AUTOMATION},
    State.REPAIRING: {State.CI_RUNNING, State.BLOCKED_AUTOMATION},
})
_BLOCKERS = {State.BLOCKED_HARDWARE, State.BLOCKED_SECRET, State.BLOCKED_PRODUCT,
             State.BLOCKED_AUTOMATION, State.STATE_INCONSISTENT}
for _state in State:
    if _state not in _BLOCKERS and _state != State.COMPLETE:
        _ALLOWED.setdefault(_state, set()).update(_BLOCKERS)


def validate_transition(current: State, target: State) -> bool:
    return target in _ALLOWED.get(current, set())


@dataclass(frozen=True)
class Binding:
    story_id: str
    baseline_sha: str
    pr: int
    expected_head_sha: str

    def valid(self) -> bool:
        return bool(self.story_id and self.baseline_sha and self.pr > 0 and self.expected_head_sha)


def execution_is_current(binding: Binding, *, story_id: str, baseline_sha: str, pr: int, head_sha: str) -> bool:
    return binding.valid() and (binding.story_id, binding.baseline_sha, binding.pr, binding.expected_head_sha) == (story_id, baseline_sha, pr, head_sha)


def next_repair_attempt(attempts: int, max_repair_attempts: int):
    if attempts < 0 or max_repair_attempts < 0 or attempts >= max_repair_attempts:
        return State.BLOCKED_AUTOMATION, attempts
    return State.REPAIRING, attempts + 1


def merge_eligible(*, binding_current: bool, ci_green: bool, security_green: bool,
                   review_approved: bool, reviewed_sha: str, tested_sha: str,
                   current_head_sha: str, pr_story_id: str, active_story_id: str,
                   blocker: str | None = None) -> bool:
    return all((binding_current, ci_green, security_green, review_approved,
                bool(current_head_sha), reviewed_sha == current_head_sha,
                tested_sha == current_head_sha, pr_story_id == active_story_id,
                not blocker))


def reconcile(*, persisted: State, pr_exists: bool, pr_merged: bool, ci_status: str | None,
              binding_current: bool) -> State:
    if not binding_current:
        return State.STATE_INCONSISTENT
    if pr_merged:
        return State.UPDATING_STATE if persisted != State.COMPLETE else State.COMPLETE
    if not pr_exists:
        return persisted if persisted in {State.READY, State.PLANNING, State.IMPLEMENTING} else State.STATE_INCONSISTENT
    mapping = {"running": State.CI_RUNNING, "failed": State.CI_FAILED, "green": State.REVIEWING}
    return mapping.get(ci_status, State.STATE_INCONSISTENT)


def hardware_verified(*, physical_evidence: bool, ci_passed: bool=False, mock_passed: bool=False,
                      simulation_passed: bool=False, ai_claimed_success: bool=False) -> bool:
    del ci_passed, mock_passed, simulation_passed, ai_claimed_success
    return physical_evidence
