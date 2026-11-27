"""Final fail-closed verification for the Queue v3 repair loop.

After mutation/rebind, fresh GitHub evidence must be for the new HEAD. The cycle
then either returns to bounded repair, waits, or reaches the existing merge gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from orchestrator_queue_v3 import QueuePlan
from orchestrator_queue_v3_autopilot import AutopilotDecision, decide_autopilot_cycle
from orchestrator_queue_v3_cycle import QueueObservation
from orchestrator_state import PersistedState
from orchestrator_v2 import GitHubEvidence, State


@dataclass(frozen=True)
class LoopVerification:
    decision: AutopilotDecision
    verified_head_sha: str


def verify_repaired_head(
    *,
    plan: QueuePlan,
    persisted: PersistedState,
    evidence: GitHubEvidence,
    ci_status: str,
    pr: dict | None = None,
    checks: list[dict] | None = None,
    reviews: list[dict] | None = None,
    required_checks: set[str] | None = None,
    security_checks: set[str] | None = None,
    protected_change: bool = False,
    security_review_for_head: bool = False,
) -> LoopVerification:
    persisted.validate()
    if persisted.state != State.CI_RUNNING:
        raise ValueError("loop-verify-ci-running-required")
    if evidence.head_sha != persisted.expected_head_sha:
        raise ValueError("loop-verify-stale-evidence")
    decision = decide_autopilot_cycle(
        plan=plan,
        persisted=persisted,
        observation=QueueObservation(persisted.baseline_sha, ci_status),
        evidence=evidence,
        pr=pr,
        checks=checks,
        reviews=reviews,
        required_checks=required_checks,
        security_checks=security_checks,
        protected_change=protected_change,
        security_review_for_head=security_review_for_head,
    )
    return LoopVerification(decision, evidence.head_sha)
