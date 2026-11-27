"""Fail-closed Queue v3 acceptance of bounded executor repair results.

The result remains a proposal. Successful acceptance only returns the validated
output and next lifecycle intent; it does not apply a patch, push, merge, or touch
hardware/secrets.
"""

from __future__ import annotations

from dataclasses import dataclass

from orchestrator_control_plane import AcceptedExecutorOutput, InvocationPlan, accept_result
from orchestrator_state import PersistedState
from orchestrator_v2 import State, validate_transition


@dataclass(frozen=True)
class RepairResultDecision:
    accepted: AcceptedExecutorOutput
    next_state: State
    ready_for_application: bool


def accept_repair_result(
    *,
    persisted: PersistedState,
    plan: InvocationPlan,
    result_payload: dict,
) -> RepairResultDecision:
    """Validate a repair result and expose only a bounded next-state decision."""
    persisted.validate()
    if persisted.state != State.REPAIRING:
        raise ValueError("repair-result-state-required")
    accepted = accept_result(persisted=persisted, plan=plan, result_payload=result_payload)
    if accepted.status != "EXECUTOR_RESULT_READY":
        return RepairResultDecision(accepted, accepted.state, False)
    if accepted.output_type != "patch-proposal":
        raise ValueError("repair-result-patch-required")
    if not validate_transition(State.REPAIRING, State.CI_RUNNING):
        raise ValueError("repair-result-invalid-transition")
    return RepairResultDecision(accepted, State.CI_RUNNING, True)
