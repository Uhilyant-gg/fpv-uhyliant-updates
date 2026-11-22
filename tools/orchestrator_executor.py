"""Bounded contract for invoking an untrusted AI executor.

The deterministic control plane creates an allowlisted request and validates the executor
result. The executor never receives merge, secret, hardware, or direct-main authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from orchestrator_v2 import State

_ALLOWED_OUTPUTS={"patch-proposal","test-plan","diagnostic-summary"}
_STOP_REASONS={"PHYSICAL_ACTION_REQUIRED","SECRET_REQUIRED","PRODUCT_DECISION_REQUIRED"}

@dataclass(frozen=True)
class ExecutorRequest:
    story_id:str
    baseline_sha:str
    state:State
    objective:str
    max_steps:int
    allowed_outputs:tuple[str,...]

    def validate(self)->None:
        if not self.story_id or not self.baseline_sha or not self.objective.strip():raise ValueError("incomplete executor request")
        if self.state not in {State.PLANNING,State.IMPLEMENTING,State.REPAIRING}:raise ValueError("executor state not allowed")
        if not 1<=self.max_steps<=20:raise ValueError("invalid executor step budget")
        if not self.allowed_outputs or any(x not in _ALLOWED_OUTPUTS for x in self.allowed_outputs):raise ValueError("executor output not allowed")

@dataclass(frozen=True)
class ExecutorResult:
    story_id:str
    baseline_sha:str
    steps_used:int
    output_type:str
    payload:str
    stop_reason:str|None=None


def validate_result(request:ExecutorRequest,result:ExecutorResult)->str:
    request.validate()
    if (result.story_id,result.baseline_sha)!=(request.story_id,request.baseline_sha):raise ValueError("stale executor result")
    if result.steps_used<0 or result.steps_used>request.max_steps:raise ValueError("executor budget exceeded")
    if result.output_type not in request.allowed_outputs:raise ValueError("executor output not authorized")
    if result.stop_reason is not None and result.stop_reason not in _STOP_REASONS:raise ValueError("unknown executor stop reason")
    if not result.payload.strip():raise ValueError("empty executor result")
    return result.stop_reason or "EXECUTOR_RESULT_READY"
