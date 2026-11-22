"""Versioned persisted state and deterministic Orchestrator v2 reconciliation CLI."""
from __future__ import annotations
import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from orchestrator_v2 import Binding, GitHubEvidence, State, merge_eligible_from_evidence, reconcile_evidence

SCHEMA_VERSION=1

@dataclass(frozen=True)
class PersistedState:
    schema_version:int
    state:State
    story_id:str
    baseline_sha:str
    pr:int
    expected_head_sha:str
    repair_attempts:int=0
    max_repair_attempts:int=3

    def validate(self)->None:
        if self.schema_version!=SCHEMA_VERSION: raise ValueError("unsupported schema_version")
        if not Binding(self.story_id,self.baseline_sha,self.pr,self.expected_head_sha).valid(): raise ValueError("invalid execution binding")
        if self.repair_attempts<0 or self.max_repair_attempts<0 or self.repair_attempts>self.max_repair_attempts: raise ValueError("invalid repair budget")

    @property
    def binding(self)->Binding:return Binding(self.story_id,self.baseline_sha,self.pr,self.expected_head_sha)


def load_state(path:Path)->PersistedState:
    raw=json.loads(path.read_text(encoding="utf-8"))
    allowed={"schema_version","state","story_id","baseline_sha","pr","expected_head_sha","repair_attempts","max_repair_attempts"}
    if set(raw)-allowed: raise ValueError("unknown persisted state fields")
    raw["state"]=State(raw["state"])
    state=PersistedState(**raw); state.validate(); return state


def save_state(path:Path,state:PersistedState)->None:
    state.validate(); path.parent.mkdir(parents=True,exist_ok=True)
    payload=asdict(state); payload["state"]=state.state.value
    with NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as handle:
        json.dump(payload,handle,sort_keys=True,indent=2); handle.write("\n"); temp=Path(handle.name)
    os.replace(temp,path)


def load_evidence(path:Path)->GitHubEvidence:
    raw=json.loads(path.read_text(encoding="utf-8"))
    allowed=set(GitHubEvidence.__dataclass_fields__)
    if set(raw)!=allowed: raise ValueError("GitHub evidence fields must exactly match schema")
    evidence=GitHubEvidence(**raw)
    if not evidence.complete(): raise ValueError("incomplete GitHub evidence")
    return evidence


def evaluate(state:PersistedState,evidence:GitHubEvidence,ci_status:str|None,pr_exists=True,pr_merged=False)->dict:
    reconciled=reconcile_evidence(persisted=state.state,binding=state.binding,evidence=evidence,pr_exists=pr_exists,pr_merged=pr_merged,ci_status=ci_status)
    eligible=merge_eligible_from_evidence(state.binding,evidence)
    return {"schemaVersion":1,"state":reconciled.value,"mergeEligible":eligible,"storyId":state.story_id,"baselineSha":state.baseline_sha,"pr":state.pr,"expectedHeadSha":state.expected_head_sha,"observedHeadSha":evidence.head_sha,"reasonCode":"ready-to-merge" if eligible else ("state-inconsistent" if reconciled==State.STATE_INCONSISTENT else "not-merge-eligible")}


def main()->int:
    parser=argparse.ArgumentParser(description="Deterministic Orchestrator v2 state reconciler")
    parser.add_argument("--state",type=Path,required=True); parser.add_argument("--evidence",type=Path,required=True)
    parser.add_argument("--ci-status",choices=("running","failed","green")); parser.add_argument("--pr-merged",action="store_true"); parser.add_argument("--pr-missing",action="store_true")
    args=parser.parse_args()
    try: result=evaluate(load_state(args.state),load_evidence(args.evidence),args.ci_status,not args.pr_missing,args.pr_merged)
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({"schemaVersion":1,"state":State.STATE_INCONSISTENT.value,"mergeEligible":False,"reasonCode":"invalid-state-or-evidence","summary":str(exc)},sort_keys=True)); return 2
    print(json.dumps(result,sort_keys=True)); return 0 if result["state"]!=State.STATE_INCONSISTENT.value else 3

if __name__=="__main__":raise SystemExit(main())
