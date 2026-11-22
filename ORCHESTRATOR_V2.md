# Orchestrator v2

## Purpose
Orchestrator v2 automates repository development while keeping authority in a deterministic control plane. AI is a replaceable untrusted executor: AI proposes; deterministic policy decides; GitHub enforces.

## Architecture
The control plane owns persisted lifecycle state, reconciliation with GitHub, transition validation, retry budgets, stale-execution protection, security policy and merge eligibility. GitHub Actions remains the execution infrastructure. AI is invoked only for bounded planning, implementation and repair work and has no independent merge or hardware authority.

Lifecycle: roadmap -> Story selection -> implementation -> tests -> PR -> CI -> bounded repair -> security/review gate -> merge -> project-state update -> next Story.

No database, event bus, Kubernetes, custom CI platform, dashboard or provider framework is required for Phase 1. State is a small versioned JSON document.

## States and execution binding
The minimal states remain `READY`, `PLANNING`, `IMPLEMENTING`, `PR_OPEN`, `CI_RUNNING`, `CI_FAILED`, `REPAIRING`, `REVIEWING`, `READY_TO_MERGE`, `MERGING`, `UPDATING_STATE`, `BLOCKED_HARDWARE`, `BLOCKED_SECRET`, `BLOCKED_PRODUCT`, `BLOCKED_AUTOMATION`, `STATE_INCONSISTENT`, `COMPLETE`.

Transitions are allowlisted and invalid transitions fail closed. Every privileged repository mutation is bound to `story_id`, `baseline_sha`, PR number and `expected_head_sha`.

## Persisted state and deterministic recovery
`tools/orchestrator_state.py` defines schema version 1 for the minimal persisted lifecycle state. Reads reject unknown schema fields, invalid bindings and invalid repair budgets. Writes use atomic replacement. The state contains no model/provider session data or secrets.

The CLI consumes a separate normalized factual GitHub evidence document. Evidence must contain exactly the expected PR/base/HEAD/Story/required-CI/security/review/reviewed-SHA/tested-SHA/blocker fields. Missing or additional evidence fails closed rather than being guessed.

Reconciliation compares persisted binding to factual GitHub evidence. A mismatch in Story, baseline, PR or HEAD becomes `STATE_INCONSISTENT`. This recovery path has no AI dependency.

## Repair and merge gates
Repair remains inside the same Story/PR and `repair_attempts` cannot exceed `max_repair_attempts`; exhaustion becomes `BLOCKED_AUTOMATION`.

Merge eligibility requires all of: current execution binding; required CI green; security green; required review approved; reviewed SHA equals current HEAD; tested SHA equals current HEAD; PR Story equals active Story; and no blocker. AI assertions cannot populate authoritative evidence.

## Protected files and workflow integrity
Canonical/control-plane documents, Orchestrator policy code/tests and `.github/workflows/**` are treated as protected security scope. Such changes require explicit security evidence and cannot silently auto-merge.

Agentic `.md` workflow source is canonical. Generated `.lock.yml` is never hand-edited. Existing gh-aw generated workflows already carry generated metadata, pinned actions/containers and stale-lock checks. `tools/check_agentic_workflow_integrity.py` adds repository-side fail-closed validation without attempting to bypass the reviewed compiler/toolchain boundary.

## Hardware boundary
CI, mocks, simulation and AI claims are never `HARDWARE_VERIFIED`. Physical or destructive hardware work requires explicit authority and otherwise becomes `BLOCKED_HARDWARE` / `PHYSICAL_ACTION_REQUIRED`.

## Security invariants
INV-01 AI never writes directly to main. INV-02 AI never receives production secrets. INV-03 AI output is always untrusted. INV-04 merge decisions are deterministic. INV-05 approval is bound to exact SHA. INV-06 control-plane/generated security files cannot silently auto-merge. INV-07 hardware verification requires physical evidence. INV-08 destructive hardware actions require explicit authority. INV-09 network access is deny-by-default where applicable. INV-10 critical runtimes/dependencies require integrity verification. INV-11 autonomous loops are bounded. INV-12 state transitions are validated. INV-13 stale executions cannot mutate current state. INV-14 security ambiguity fails closed. INV-15 recovery must not require an available AI engine.

## Stop reasons
`PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, `PRODUCT_DECISION_REQUIRED`, `SECURITY_REVIEW_REQUIRED`, `STATE_INCONSISTENT`, `STALE_EXECUTION`, `AI_ENGINE_UNAVAILABLE`, `AUTOMATION_BUDGET_EXCEEDED`.
