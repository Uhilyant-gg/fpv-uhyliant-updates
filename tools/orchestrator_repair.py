"""Deterministic bounded repair decision policy."""
from dataclasses import dataclass
from orchestrator_v2 import Binding,GitHubEvidence,State,evidence_binding_current,next_repair_attempt

@dataclass(frozen=True)
class RepairDecision:
    state:State
    attempts:int
    reason_code:str
    invoke_ai:bool


def decide_repair(binding:Binding,evidence:GitHubEvidence,*,ci_status:str,attempts:int,max_attempts:int)->RepairDecision:
    if not evidence_binding_current(binding,evidence):return RepairDecision(State.STATE_INCONSISTENT,attempts,"stale-execution",False)
    if evidence.blocker and evidence.blocker not in {"required-check-failed"}:return RepairDecision(State.BLOCKED_AUTOMATION,attempts,evidence.blocker,False)
    if ci_status!="failed":return RepairDecision(State.STATE_INCONSISTENT,attempts,"repair-without-ci-failure",False)
    state,new_attempts=next_repair_attempt(attempts,max_attempts)
    if state==State.BLOCKED_AUTOMATION:return RepairDecision(state,new_attempts,"automation-budget-exceeded",False)
    return RepairDecision(state,new_attempts,"repair-authorized",True)
