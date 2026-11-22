"""GitHub Actions adapter for deterministic Orchestrator v2 merge authority.

The workflow gathers GitHub facts. This module validates the event binding, normalizes
checks/reviews through the existing collector and emits a decision. It never merges.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from orchestrator_github_evidence import collect
from orchestrator_v2 import Binding,merge_eligible_from_evidence


def evaluate_event(*,event:dict,checks:list[dict],reviews:list[dict],required_checks:set[str],security_checks:set[str],story_id:str,expected_head_sha:str|None=None)->dict:
    pr=event.get("pull_request") or {}
    number=pr.get("number") or event.get("number")
    head=(pr.get("head") or {}).get("sha")
    base=(pr.get("base") or {}).get("sha")
    if not isinstance(number,int) or not head or not base:raise ValueError("pull_request event identity required")
    if expected_head_sha and expected_head_sha!=head:return {"mergeEligible":False,"reasonCode":"stale-execution","headSha":head}
    evidence,reason=collect(pr={"number":number,"head":{"sha":head},"base":{"sha":base}},checks=checks,reviews=reviews,required_checks=required_checks,security_checks=security_checks,story_id=story_id)
    binding=Binding(story_id,base,number,head)
    eligible=merge_eligible_from_evidence(binding,evidence)
    return {"mergeEligible":eligible,"reasonCode":"ready-to-merge" if eligible else reason,"pr":number,"storyId":story_id,"baselineSha":base,"headSha":head,"testedSha":evidence.tested_sha,"reviewedSha":evidence.reviewed_sha}


def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--event",type=Path,required=True);p.add_argument("--checks",type=Path,required=True);p.add_argument("--reviews",type=Path,required=True);p.add_argument("--story-id",required=True);p.add_argument("--expected-head-sha");p.add_argument("--required-check",action="append",default=[]);p.add_argument("--security-check",action="append",default=[]);p.add_argument("--github-output",type=Path)
    a=p.parse_args()
    try:
        result=evaluate_event(event=json.loads(a.event.read_text()),checks=json.loads(a.checks.read_text()),reviews=json.loads(a.reviews.read_text()),required_checks=set(a.required_check),security_checks=set(a.security_check),story_id=a.story_id,expected_head_sha=a.expected_head_sha)
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        result={"mergeEligible":False,"reasonCode":"invalid-github-evidence","summary":str(exc)}
    print(json.dumps(result,sort_keys=True))
    if a.github_output:
        with a.github_output.open("a",encoding="utf-8") as f:
            f.write("merge_eligible="+("true" if result["mergeEligible"] else "false")+"\n")
            f.write("reason_code="+result["reasonCode"]+"\n")
            f.write("head_sha="+str(result.get("headSha", ""))+"\n")
    return 0 if result["mergeEligible"] else 3
if __name__=="__main__":sys.exit(main())
