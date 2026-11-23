"""Fail-closed Queue v3 bridge to the bounded repair policy.

A Queue v3 REPAIR decision is only an intent. This layer requires current GitHub
evidence and the persisted repair budget before repair invocation may be authorized.
"""
from __future__ import annotations

from dataclasses import dataclass

from orchestrator_queue_v3_runner import QueueAction, QueueDecision
from orchestrator_repair import RepairDecision, decide_repair
from orchestrator_state import PersistedState
from orchestrator_v2 import GitHubEvidence


@dataclass(frozen=True)
class RepairAuthorization:
    decision: RepairDecision
    authorized: bool


def authorize_repair(
    *,
    queue_decision: QueueDecision,
    persisted: PersistedState,
    evidence: GitHubEvidence,
    ci_status: str,
) -> RepairAuthorization:
    """Authorize bounded repair only for a current Queue v3 REPAIR intent."""
    persisted.validate()
    if queue_decision.action != QueueAction.REPAIR:
        raise ValueError("queue-repair-intent-required")
    if queue_decision.reason_code != "repair-current-batch":
        raise ValueError("queue-repair-reason-mismatch")
    repair = decide_repair(
        persisted.binding,
        evidence,
        ci_status=ci_status,
        attempts=persisted.repair_attempts,
        max_attempts=persisted.max_repair_attempts,
    )
    return RepairAuthorization(repair, repair.invoke_ai)
