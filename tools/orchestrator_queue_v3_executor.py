"""Fail-closed Queue v3 handoff into the bounded executor control plane.

Only a previously authorized REPAIR action may create an executor invocation plan.
The executor remains untrusted and cannot merge, access secrets, or prove hardware.
"""

from __future__ import annotations

from orchestrator_control_plane import InvocationPlan, prepare_invocation
from orchestrator_queue_v3_autopilot import AutopilotAction, AutopilotDecision
from orchestrator_state import PersistedState
from orchestrator_v2 import State


def prepare_repair_handoff(
    *,
    decision: AutopilotDecision,
    persisted: PersistedState,
    objective: str,
    max_steps: int = 8,
    allowed_outputs: list[str] | None = None,
) -> InvocationPlan:
    persisted.validate()
    if decision.action != AutopilotAction.REPAIR:
        raise ValueError("executor-repair-authorization-required")
    if decision.reason_code != "repair-authorized":
        raise ValueError("executor-repair-reason-mismatch")
    if persisted.state != State.REPAIRING:
        raise ValueError("executor-repair-state-required")
    return prepare_invocation(
        persisted=persisted,
        objective=objective,
        max_steps=max_steps,
        allowed_outputs=allowed_outputs,
    )
