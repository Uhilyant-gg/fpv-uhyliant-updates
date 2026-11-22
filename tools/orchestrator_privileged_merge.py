"""Final deterministic authorization immediately before a privileged GitHub merge.

This module does not call GitHub. The workflow fetches fresh facts, this policy validates
them, and only then may the workflow invoke the GitHub merge API with expected HEAD SHA.
"""
from __future__ import annotations
from dataclasses import dataclass
from orchestrator_github_evidence import collect
from orchestrator_v2 import Binding,merge_eligible_from_evidence

@dataclass(frozen=True)
class MergeAuthorization:
    authorized:bool
    reason_code:str
    pr:int
    expected_head_sha:str


def authorize(*,binding:Binding,pr:dict,checks:list[dict],reviews:list[dict],required_checks:set[str],security_checks:set[str],story_id:str,protected_change:bool,security_review_for_head:bool)->MergeAuthorization:
    if not binding.valid():return MergeAuthorization(False,"invalid-binding",binding.pr,binding.expected_head_sha)
    head=(pr.get("head") or {}).get("sha");base=(pr.get("base") or {}).get("sha");number=pr.get("number")
    if (story_id,base,number,head)!=(binding.story_id,binding.baseline_sha,binding.pr,binding.expected_head_sha):return MergeAuthorization(False,"stale-execution",binding.pr,binding.expected_head_sha)
    if protected_change and not security_review_for_head:return MergeAuthorization(False,"security-review-required",number,head)
    evidence,reason=collect(pr=pr,checks=checks,reviews=reviews,required_checks=required_checks,security_checks=security_checks,story_id=story_id)
    if not merge_eligible_from_evidence(binding,evidence):return MergeAuthorization(False,reason,number,head)
    return MergeAuthorization(True,"merge-authorized",number,head)
