"""Normalize GitHub API JSON into strict Orchestrator v2 evidence.

This module is deliberately transport-agnostic: a workflow supplies factual PR/check/review
JSON fetched from GitHub. The collector never calls AI and never guesses missing evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from orchestrator_v2 import GitHubEvidence

_SUCCESS={"success","neutral","skipped"}
_PENDING={"queued","in_progress","pending","requested","waiting"}
_FAILURE={"failure","cancelled","timed_out","action_required","startup_failure","stale"}
_APPROVED="APPROVED"


def _required_checks(checks:list[dict],required:set[str])->tuple[bool,str|None,str]:
    by_name={}
    for item in checks:
        name=item.get("name")
        if name in by_name: return False,None,"duplicate-required-check" if name in required else "duplicate-check"
        by_name[name]=item
    if not required:return False,None,"required-check-policy-empty"
    missing=sorted(required-set(by_name))
    if missing:return False,None,"required-check-missing"
    tested={item.get("head_sha") for name,item in by_name.items() if name in required}
    if len(tested)!=1 or None in tested:return False,None,"tested-sha-ambiguous"
    for name in required:
        item=by_name[name]; status=item.get("status"); conclusion=item.get("conclusion")
        if status!="completed":return False,None,"required-check-running" if status in _PENDING else "required-check-unknown"
        if conclusion not in _SUCCESS:return False,None,"required-check-failed" if conclusion in _FAILURE else "required-check-unknown"
    return True,next(iter(tested)),"green"


def _review(reviews:list[dict],head_sha:str)->tuple[bool,str]:
    authoritative=[r for r in reviews if r.get("state") in {_APPROVED,"CHANGES_REQUESTED","DISMISSED"}]
    if not authoritative:return False,""
    latest={}
    for r in authoritative:
        user=(r.get("user") or {}).get("login")
        if not user:return False,""
        latest[user]=r
    approved=[r for r in latest.values() if r.get("state")==_APPROVED and r.get("commit_id")==head_sha]
    blocking=any(r.get("state")=="CHANGES_REQUESTED" for r in latest.values())
    return bool(approved) and not blocking, head_sha if approved and not blocking else ""


def collect(*,pr:dict,checks:list[dict],reviews:list[dict],required_checks:set[str],security_checks:set[str],story_id:str,require_review:bool=True)->tuple[GitHubEvidence,str]:
    number=pr.get("number"); head=((pr.get("head") or {}).get("sha")); base=((pr.get("base") or {}).get("sha"))
    if not isinstance(number,int) or number<=0 or not head or not base or not story_id:raise ValueError("incomplete PR identity evidence")
    required_green,tested_sha,ci_reason=_required_checks(checks,required_checks)
    security_green,security_tested,security_reason=_required_checks(checks,security_checks)
    review_approved,reviewed_sha=_review(reviews,head)
    blocker=None
    if not required_green:blocker=ci_reason
    elif not security_green:blocker=security_reason
    elif tested_sha!=head or security_tested!=head:blocker="tested-sha-stale"
    elif require_review and not review_approved:blocker="review-not-approved-for-head"
    evidence=GitHubEvidence(number,head,base,story_id,required_green,security_green,review_approved,reviewed_sha,tested_sha or "",blocker)
    return evidence, blocker or "ready"


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--pr",type=Path,required=True); p.add_argument("--checks",type=Path,required=True); p.add_argument("--reviews",type=Path,required=True); p.add_argument("--story-id",required=True); p.add_argument("--required-check",action="append",default=[]); p.add_argument("--security-check",action="append",default=[]); p.add_argument("--output",type=Path)
    a=p.parse_args()
    try:
        pr=json.loads(a.pr.read_text(encoding="utf-8")); checks=json.loads(a.checks.read_text(encoding="utf-8")); reviews=json.loads(a.reviews.read_text(encoding="utf-8"))
        evidence,reason=collect(pr=pr,checks=checks,reviews=reviews,required_checks=set(a.required_check),security_checks=set(a.security_check),story_id=a.story_id)
        payload=evidence.__dict__
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(json.dumps({"status":"STATE_INCONSISTENT","reasonCode":"invalid-github-evidence","summary":str(exc)},sort_keys=True)); return 2
    text=json.dumps(payload,sort_keys=True,indent=2)+"\n"
    if a.output:a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    return 0 if reason=="ready" else 3
if __name__=="__main__":raise SystemExit(main())
