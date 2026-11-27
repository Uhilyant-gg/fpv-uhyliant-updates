"""Deterministic Orchestrator v2 control-plane primitives.

No AI/provider code belongs here. Inputs are factual evidence gathered by a caller;
policy is pure and fail-closed so recovery does not depend on an AI engine.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath


class State(str, Enum):
    READY = "READY"
    PLANNING = "PLANNING"
    IMPLEMENTING = "IMPLEMENTING"
    PR_OPEN = "PR_OPEN"
    CI_RUNNING = "CI_RUNNING"
    CI_FAILED = "CI_FAILED"
    REPAIRING = "REPAIRING"
    REVIEWING = "REVIEWING"
    READY_TO_MERGE = "READY_TO_MERGE"
    MERGING = "MERGING"
    UPDATING_STATE = "UPDATING_STATE"
    BLOCKED_HARDWARE = "BLOCKED_HARDWARE"
    BLOCKED_SECRET = "BLOCKED_SECRET"
    BLOCKED_PRODUCT = "BLOCKED_PRODUCT"
    BLOCKED_AUTOMATION = "BLOCKED_AUTOMATION"
    STATE_INCONSISTENT = "STATE_INCONSISTENT"
    COMPLETE = "COMPLETE"


FLOW = [
    State.READY,
    State.PLANNING,
    State.IMPLEMENTING,
    State.PR_OPEN,
    State.CI_RUNNING,
    State.REVIEWING,
    State.READY_TO_MERGE,
    State.MERGING,
    State.UPDATING_STATE,
    State.COMPLETE,
]
_ALLOWED = {s: {FLOW[i + 1]} for i, s in enumerate(FLOW[:-1])}
_ALLOWED.update(
    {
        State.CI_RUNNING: {State.CI_FAILED, State.REVIEWING},
        State.CI_FAILED: {State.REPAIRING, State.BLOCKED_AUTOMATION},
        State.REPAIRING: {State.CI_RUNNING, State.BLOCKED_AUTOMATION},
    }
)
_BLOCKERS = {
    State.BLOCKED_HARDWARE,
    State.BLOCKED_SECRET,
    State.BLOCKED_PRODUCT,
    State.BLOCKED_AUTOMATION,
    State.STATE_INCONSISTENT,
}
for _state in State:
    if _state not in _BLOCKERS and _state != State.COMPLETE:
        _ALLOWED.setdefault(_state, set()).update(_BLOCKERS)

PROTECTED_EXACT = {
    "ORCHESTRATOR_V2.md",
    "AUTONOMOUS_DEVELOPMENT.md",
    "DEVELOPMENT_GUIDE.md",
    "PROJECT_STATE.md",
    "DELIVERY_ROADMAP.md",
    "PRODUCT_UX.md",
    "HARDWARE_E2E.md",
}
PROTECTED_PREFIXES = (
    ".github/workflows/",
    "tools/orchestrator_v2.py",
    "tools/check_orchestrator_security.py",
    "features/orchestrator_v2_security.feature",
)


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


@dataclass(frozen=True)
class GitHubEvidence:
    pr: int
    head_sha: str
    base_sha: str
    pr_story_id: str
    required_ci_green: bool
    security_green: bool
    review_approved: bool
    reviewed_sha: str
    tested_sha: str
    blocker: str | None = None

    def complete(self) -> bool:
        return bool(self.pr > 0 and self.head_sha and self.base_sha and self.pr_story_id)


def execution_is_current(binding: Binding, *, story_id: str, baseline_sha: str, pr: int, head_sha: str) -> bool:
    return binding.valid() and (binding.story_id, binding.baseline_sha, binding.pr, binding.expected_head_sha) == (
        story_id,
        baseline_sha,
        pr,
        head_sha,
    )


def evidence_binding_current(binding: Binding, evidence: GitHubEvidence) -> bool:
    return evidence.complete() and execution_is_current(
        binding,
        story_id=evidence.pr_story_id,
        baseline_sha=evidence.base_sha,
        pr=evidence.pr,
        head_sha=evidence.head_sha,
    )


def next_repair_attempt(attempts: int, max_repair_attempts: int):
    if attempts < 0 or max_repair_attempts < 0 or attempts >= max_repair_attempts:
        return State.BLOCKED_AUTOMATION, attempts
    return State.REPAIRING, attempts + 1


def merge_eligible(
    *,
    binding_current: bool,
    ci_green: bool,
    security_green: bool,
    review_approved: bool,
    reviewed_sha: str,
    tested_sha: str,
    current_head_sha: str,
    pr_story_id: str,
    active_story_id: str,
    blocker: str | None = None,
) -> bool:
    return all(
        (
            binding_current,
            ci_green,
            security_green,
            review_approved,
            bool(current_head_sha),
            reviewed_sha == current_head_sha,
            tested_sha == current_head_sha,
            pr_story_id == active_story_id,
            not blocker,
        )
    )


def merge_eligible_from_evidence(binding: Binding, evidence: GitHubEvidence) -> bool:
    return merge_eligible(
        binding_current=evidence_binding_current(binding, evidence),
        ci_green=evidence.required_ci_green,
        security_green=evidence.security_green,
        review_approved=evidence.review_approved,
        reviewed_sha=evidence.reviewed_sha,
        tested_sha=evidence.tested_sha,
        current_head_sha=evidence.head_sha,
        pr_story_id=evidence.pr_story_id,
        active_story_id=binding.story_id,
        blocker=evidence.blocker,
    )


def reconcile(
    *, persisted: State, pr_exists: bool, pr_merged: bool, ci_status: str | None, binding_current: bool
) -> State:
    if not binding_current:
        return State.STATE_INCONSISTENT
    if pr_merged:
        return State.UPDATING_STATE if persisted != State.COMPLETE else State.COMPLETE
    if not pr_exists:
        return persisted if persisted in {State.READY, State.PLANNING, State.IMPLEMENTING} else State.STATE_INCONSISTENT
    return {"running": State.CI_RUNNING, "failed": State.CI_FAILED, "green": State.REVIEWING}.get(
        ci_status, State.STATE_INCONSISTENT
    )


def reconcile_evidence(
    *,
    persisted: State,
    binding: Binding,
    evidence: GitHubEvidence,
    pr_exists: bool = True,
    pr_merged: bool = False,
    ci_status: str | None = None,
) -> State:
    return reconcile(
        persisted=persisted,
        pr_exists=pr_exists,
        pr_merged=pr_merged,
        ci_status=ci_status,
        binding_current=evidence_binding_current(binding, evidence),
    )


def is_protected_path(path: str) -> bool:
    normalized = str(PurePosixPath(path.replace('\\', '/')))
    if normalized.startswith('../') or normalized.startswith('/'):
        return True
    return normalized in PROTECTED_EXACT or normalized.startswith(PROTECTED_PREFIXES)


def protected_change_requires_security_review(paths: list[str]) -> bool:
    return any(is_protected_path(path) for path in paths)


def hardware_verified(
    *,
    physical_evidence: bool,
    ci_passed: bool = False,
    mock_passed: bool = False,
    simulation_passed: bool = False,
    ai_claimed_success: bool = False,
) -> bool:
    del ci_passed, mock_passed, simulation_passed, ai_claimed_success
    return physical_evidence
