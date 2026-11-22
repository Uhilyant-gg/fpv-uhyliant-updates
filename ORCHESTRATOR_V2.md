# Orchestrator v2

## Purpose
Orchestrator v2 automates the repository development lifecycle while keeping authority in a deterministic control plane. AI is a replaceable untrusted executor: AI proposes; deterministic policy decides; GitHub enforces.

## Architecture
The control plane owns persisted lifecycle state, reconciliation with GitHub, transition validation, retry budgets, stale-execution protection, security policy and merge eligibility. GitHub Actions is the execution infrastructure. AI is invoked only for bounded planning/implementation/repair work and has no independent merge or hardware authority.

Lifecycle: roadmap -> Story selection -> implementation -> tests -> PR -> CI -> bounded repair -> security/review gate -> merge -> project-state update -> next Story.

No database, event bus, Kubernetes, custom CI platform, dashboard or provider framework is required for Phase 1. State is a small versioned JSON document suitable for repository/workflow artifacts.

## Minimal states
`READY`, `PLANNING`, `IMPLEMENTING`, `PR_OPEN`, `CI_RUNNING`, `CI_FAILED`, `REPAIRING`, `REVIEWING`, `READY_TO_MERGE`, `MERGING`, `UPDATING_STATE`, `BLOCKED_HARDWARE`, `BLOCKED_SECRET`, `BLOCKED_PRODUCT`, `BLOCKED_AUTOMATION`, `STATE_INCONSISTENT`, `COMPLETE`.

Transitions are allowlisted. Invalid transitions fail closed.

## Execution binding
Every privileged repository mutation is bound to `story_id`, `baseline_sha`, PR number and `expected_head_sha`. A mismatch with current GitHub evidence is stale execution and cannot mutate current state.

## Reconciliation
Restart/re-entry compares persisted state with factual GitHub PR/HEAD/CI/review evidence. A uniquely supported lifecycle state may be restored without AI. Missing, contradictory or ambiguous evidence becomes `STATE_INCONSISTENT`.

Recovery of deterministic state never requires an AI engine.

## Repair loop
CI repair stays on the same Story and PR. `repair_attempts` is incremented before another AI repair attempt and cannot exceed `max_repair_attempts`. Exhaustion becomes `BLOCKED_AUTOMATION`.

## Merge gate
Merge eligibility is deterministic and requires all of:
- required CI green;
- security green;
- required review approved;
- reviewed SHA equals current PR HEAD;
- tested SHA equals current PR HEAD;
- PR Story equals active Story;
- execution binding is current;
- no blocker.

AI output cannot satisfy any of these evidence fields by assertion.

## Hardware boundary
CI, mocks, simulation and AI claims are never `HARDWARE_VERIFIED`. Physical or destructive hardware work requires explicit authority and otherwise becomes `BLOCKED_HARDWARE` / `PHYSICAL_ACTION_REQUIRED`.

## Workflow integrity
`.github/workflows/*.md` is canonical for agentic workflows. Generated `.lock.yml` is never hand-edited. CI must compile the canonical source with `gh aw compile` and fail when the generated output differs. If a required runtime/dependency has no reviewed integrity pin, fail closed rather than bypass verification.

## Threat model
Treat AI output, prompts, retrieved repository text, MCP/tool responses, PR content and external dependency metadata as potentially hostile or malformed. Threats include prompt injection, secret disclosure, stale runs, forged success, review-to-HEAD races, CI-to-HEAD races, generated-workflow drift, protected-file mutation, supply-chain substitution, network exfiltration, unbounded repair loops, provider failure and fabricated hardware evidence.

## Security invariants
- INV-01 AI never writes directly to main.
- INV-02 AI never receives production secrets.
- INV-03 AI output is always untrusted.
- INV-04 Merge decisions are deterministic.
- INV-05 Approval is bound to exact SHA.
- INV-06 Control-plane/generated security files cannot silently auto-merge.
- INV-07 Hardware verification requires physical evidence.
- INV-08 Destructive hardware actions require explicit authority.
- INV-09 Network access is deny-by-default where applicable.
- INV-10 Critical runtimes/dependencies require integrity verification.
- INV-11 Autonomous loops are bounded.
- INV-12 State transitions are validated.
- INV-13 Stale executions cannot mutate current state.
- INV-14 Security ambiguity fails closed.
- INV-15 Recovery must not require an available AI engine.

## Stop reasons
`PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, `PRODUCT_DECISION_REQUIRED`, `SECURITY_REVIEW_REQUIRED`, `STATE_INCONSISTENT`, `STALE_EXECUTION`, `AI_ENGINE_UNAVAILABLE`, `AUTOMATION_BUDGET_EXCEEDED`.

## Phase 1 acceptance
Phase 1 is accepted when the control-plane module and executable P0 security scenarios prove transition validation, stale-run blocking, bounded repairs, deterministic merge gating, hardware boundary behavior and fail-closed ambiguity; CI executes those scenarios; and agentic workflow source/generated integrity remains an explicit gate. A passing software suite is not physical evidence.
