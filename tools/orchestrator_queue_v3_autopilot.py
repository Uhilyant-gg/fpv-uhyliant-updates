"""Composable, fail-closed Queue v3 autopilot cycle.

This module routes one observed cycle into the already-established WAIT, bounded
REPAIR, merge-authorization, REFRESH, or STOP boundaries. It performs no merge,
code mutation, provider invocation, secret access, or hardware action itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from orchestrator_queue_v3 import QueuePlan
from orchestrator_queue_v3_cycle import QueueObservation, decide_cycle
from orchestrator_queue_v3_merge import authorize_queue_merge
from orchestrator_queue_v3_repair import authorize_repair
from orchestrator_queue_v3_runner import QueueAction, QueueDecision
from orchestrator_state import PersistedState
from orchestrator_v2 import GitHubEvidence


class AutopilotAction(str, Enum):
    WAIT = "WAIT"
    REPAIR = "REPAIR"
    MERGE_AUTHORIZED = "MERGE_AUTHORIZED"
    REFRESH = "REFRESH"
    STOP = "STOP"


@dataclass(frozen=True)
class AutopilotDecision:
    action: AutopilotAction
    reason_code: str


def decide_autopilot_cycle(
    *,
    plan: QueuePlan,
    persisted: PersistedState,
    observation: QueueObservation,
    evidence: GitHubEvidence | None = None,
    pr: dict | None = None,
    checks: list[dict] | None = None,
    reviews: list[dict] | None = None,
    required_checks: set[str] | None = None,
    security_checks: set[str] | None = None,
    protected_change: bool = False,
    security_review_for_head: bool = False,
) -> AutopilotDecision:
    """Route a single cycle without bypassing existing authorization boundaries."""
    decision: QueueDecision = decide_cycle(plan=plan, persisted=persisted, observation=observation)
    if decision.action == QueueAction.STOP:
        return AutopilotDecision(AutopilotAction.STOP, decision.reason_code)
    if decision.action == QueueAction.REFRESH:
        return AutopilotDecision(AutopilotAction.REFRESH, decision.reason_code)
    if decision.action == QueueAction.REPAIR:
        if evidence is None:
            return AutopilotDecision(AutopilotAction.STOP, "repair-evidence-required")
        authorization = authorize_repair(
            queue_decision=decision,
            persisted=persisted,
            evidence=evidence,
            ci_status=observation.ci_status,
        )
        if not authorization.authorized:
            return AutopilotDecision(AutopilotAction.STOP, authorization.decision.reason_code)
        return AutopilotDecision(AutopilotAction.REPAIR, authorization.decision.reason_code)
    if decision.reason_code == "ci-in-progress":
        return AutopilotDecision(AutopilotAction.WAIT, decision.reason_code)
    if decision.reason_code != "awaiting-existing-merge-gate":
        raise ValueError("autopilot-unexpected-wait-reason")
    if pr is None or checks is None or reviews is None or required_checks is None or security_checks is None:
        return AutopilotDecision(AutopilotAction.STOP, "merge-evidence-required")
    authorization = authorize_queue_merge(
        queue_decision=decision,
        persisted=persisted,
        pr=pr,
        checks=checks,
        reviews=reviews,
        required_checks=required_checks,
        security_checks=security_checks,
        protected_change=protected_change,
        security_review_for_head=security_review_for_head,
    )
    if not authorization.authorized:
        return AutopilotDecision(AutopilotAction.STOP, authorization.reason_code)
    return AutopilotDecision(AutopilotAction.MERGE_AUTHORIZED, authorization.reason_code)
