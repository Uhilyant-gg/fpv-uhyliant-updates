"""Deterministic control-plane bridge for bounded executor invocation.

This module owns lifecycle/binding decisions around untrusted executor envelopes. It does
not call an AI provider, merge code, access secrets, or claim hardware verification.
"""
from __future__ import annotations
from dataclasses import dataclass
from orchestrator_executor_adapter import build_request,parse_result
from orchestrator_state import PersistedState
from orchestrator_v2 import State,validate_transition

_EXECUTOR_STATES={State.PLANNING,State.IMPLEMENTING,State.REPAIRING}
_STOP_TO_STATE={
    "PHYSICAL_ACTION_REQUIRED":State.BLOCKED_HARDWARE,
    "SECRET_REQUIRED":State.BLOCKED_SECRET,
    "PRODUCT_DECISION_REQUIRED":State.BLOCKED_PRODUCT,
}

@dataclass(frozen=True)
class InvocationPlan:
    request:dict
    state:State
    story_id:str
    baseline_sha:str

@dataclass(frozen=True)
class AcceptedExecutorOutput:
    status:str
    state:State
    output_type:str
    payload:str


def prepare_invocation(*,persisted:PersistedState,objective:str,max_steps:int=8,allowed_outputs:list[str]|None=None)->InvocationPlan:
    persisted.validate()
    if persisted.state not in _EXECUTOR_STATES:raise ValueError("executor invocation not allowed in current lifecycle state")
    outputs=allowed_outputs or ["patch-proposal","test-plan","diagnostic-summary"]
    request=build_request(story_id=persisted.story_id,baseline_sha=persisted.baseline_sha,state=persisted.state.value,objective=objective,max_steps=max_steps,allowed_outputs=outputs)
    return InvocationPlan(request,persisted.state,persisted.story_id,persisted.baseline_sha)


def accept_result(*,persisted:PersistedState,plan:InvocationPlan,result_payload:dict)->AcceptedExecutorOutput:
    persisted.validate()
    if (persisted.story_id,persisted.baseline_sha,persisted.state)!=(plan.story_id,plan.baseline_sha,plan.state):raise ValueError("stale control-plane invocation")
    result,status=parse_result(plan.request,result_payload)
    if status in _STOP_TO_STATE:
        target=_STOP_TO_STATE[status]
        if not validate_transition(persisted.state,target):raise ValueError("invalid blocker transition")
        return AcceptedExecutorOutput(status,target,result.output_type,result.payload)
    if status!="EXECUTOR_RESULT_READY":raise ValueError("unknown executor result status")
    return AcceptedExecutorOutput(status,persisted.state,result.output_type,result.payload)
