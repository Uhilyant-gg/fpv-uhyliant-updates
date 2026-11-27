"""Final deterministic authorization immediately before a privileged GitHub merge.

Ordinary changes may use the solo-development policy. Protected control-plane changes
still require an exact-HEAD security review plus fresh required CI/security evidence.
"""

from __future__ import annotations
from dataclasses import dataclass
from orchestrator_github_evidence import collect
from orchestrator_v2 import Binding, evidence_binding_current, merge_eligible_from_evidence


@dataclass(frozen=True)
class MergeAuthorization:
    authorized: bool
    reason_code: str
    pr: int
    expected_head_sha: str


def _solo_eligible(binding: Binding, evidence) -> bool:
    return all(
        (
            evidence_binding_current(binding, evidence),
            evidence.required_ci_green,
            evidence.security_green,
            evidence.tested_sha == evidence.head_sha,
            not evidence.blocker,
        )
    )


def authorize(
    *,
    binding: Binding,
    pr: dict,
    checks: list[dict],
    reviews: list[dict],
    required_checks: set[str],
    security_checks: set[str],
    story_id: str,
    protected_change: bool,
    security_review_for_head: bool,
) -> MergeAuthorization:
    if not binding.valid():
        return MergeAuthorization(False, "invalid-binding", binding.pr, binding.expected_head_sha)
    head = (pr.get("head") or {}).get("sha")
    base = (pr.get("base") or {}).get("sha")
    number = pr.get("number")
    if (story_id, base, number, head) != (
        binding.story_id,
        binding.baseline_sha,
        binding.pr,
        binding.expected_head_sha,
    ):
        return MergeAuthorization(False, "stale-execution", binding.pr, binding.expected_head_sha)
    if protected_change and not security_review_for_head:
        return MergeAuthorization(False, "security-review-required", number, head)
    evidence, reason = collect(
        pr=pr,
        checks=checks,
        reviews=reviews,
        required_checks=required_checks,
        security_checks=security_checks,
        story_id=story_id,
        require_review=protected_change,
    )
    eligible = (
        merge_eligible_from_evidence(binding, evidence) if protected_change else _solo_eligible(binding, evidence)
    )
    if not eligible:
        return MergeAuthorization(False, reason, number, head)
    return MergeAuthorization(True, "merge-authorized", number, head)
