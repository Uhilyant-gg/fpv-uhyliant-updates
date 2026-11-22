# Orchestrator v2

Orchestrator v2 keeps lifecycle authority in a deterministic control plane. AI proposes; deterministic policy decides; GitHub enforces. AI is replaceable and untrusted.

## Lifecycle
Roadmap -> Story -> implementation -> tests -> PR -> CI -> bounded repair -> security/review gate -> merge -> project-state update -> next Story.

States remain `READY`, `PLANNING`, `IMPLEMENTING`, `PR_OPEN`, `CI_RUNNING`, `CI_FAILED`, `REPAIRING`, `REVIEWING`, `READY_TO_MERGE`, `MERGING`, `UPDATING_STATE`, `BLOCKED_HARDWARE`, `BLOCKED_SECRET`, `BLOCKED_PRODUCT`, `BLOCKED_AUTOMATION`, `STATE_INCONSISTENT`, `COMPLETE`. Transitions are allowlisted and fail closed.

## Persisted execution binding
`tools/orchestrator_state.py` persists schema-versioned state atomically. Authority is bound to `story_id`, `baseline_sha`, PR and `expected_head_sha`. State contains no provider session or secret data. Invalid, additional or incomplete state/evidence fields fail closed.

## GitHub evidence collector
`tools/orchestrator_github_evidence.py` is transport-agnostic. Workflows fetch factual GitHub PR/check/review JSON; the collector converts it to the strict `GitHubEvidence` boundary. It never calls AI and never turns absence into success.

Required check names are policy input. Every required check must exist exactly once, be completed with an accepted successful conclusion, and report one tested SHA. Security checks are evaluated separately. Tested SHA must equal current PR HEAD. Review approval must be bound to current HEAD; a current blocking review prevents approval. Ambiguity, duplicates, missing checks, unknown statuses and stale SHAs fail closed.

The collector does not decide which checks an administrator marks required. That remains repository security policy. It only evaluates explicit policy plus GitHub facts.

## Deterministic reconciliation and merge gate
Restart/re-entry compares persisted binding with normalized GitHub evidence. Story, baseline, PR or HEAD mismatch becomes `STATE_INCONSISTENT`. Recovery needs no AI.

Merge eligibility requires current binding, required CI green, security green, required review approved, reviewed SHA == HEAD, tested SHA == HEAD, PR Story == active Story and no blocker. AI assertion cannot populate these fields.

## Bounded repair decision
`tools/orchestrator_repair.py` authorizes AI repair only when factual evidence remains bound to the same Story/baseline/PR/HEAD and CI is actually failed. A repair increments the deterministic budget before invocation. Budget exhaustion becomes `BLOCKED_AUTOMATION`; stale evidence becomes `STATE_INCONSISTENT`; non-CI blockers do not invoke AI.

## Protected/workflow integrity
Canonical/control-plane files and `.github/workflows/**` are protected security scope. Agentic `.md` is canonical and generated `.lock.yml` is never hand-edited. Existing gh-aw stale-lock/pinned-runtime machinery is reused; repository checks do not bypass reviewed integrity pins.

## Hardware boundary
CI, mocks, simulation and AI claims are never `HARDWARE_VERIFIED`. Physical/destructive hardware operation requires explicit authority.

## Invariants
INV-01 AI never writes directly to main. INV-02 AI never receives production secrets. INV-03 AI output is always untrusted. INV-04 merge decisions are deterministic. INV-05 approval is bound to exact SHA. INV-06 control-plane/generated security files cannot silently auto-merge. INV-07 hardware verification requires physical evidence. INV-08 destructive hardware actions require explicit authority. INV-09 network access is deny-by-default where applicable. INV-10 critical dependencies require integrity verification. INV-11 autonomous loops are bounded. INV-12 transitions are validated. INV-13 stale executions cannot mutate current state. INV-14 ambiguity fails closed. INV-15 recovery does not require AI.

Stop reasons: `PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, `PRODUCT_DECISION_REQUIRED`, `SECURITY_REVIEW_REQUIRED`, `STATE_INCONSISTENT`, `STALE_EXECUTION`, `AI_ENGINE_UNAVAILABLE`, `AUTOMATION_BUDGET_EXCEEDED`.
