# Orchestrator v2

Orchestrator v2 keeps lifecycle authority in a deterministic control plane. AI proposes; deterministic policy decides; GitHub enforces. AI is replaceable and untrusted.

## Lifecycle
Roadmap -> Story -> implementation -> tests -> PR -> CI -> bounded repair -> security/review gate -> merge -> project-state update -> next Story. Privileged execution is always bound to Story, baseline SHA, PR and expected HEAD SHA.

Persisted strict state, factual GitHub evidence normalization, bounded repair and deterministic post-merge handoff are implemented in `tools/orchestrator_state.py`, `tools/orchestrator_github_evidence.py`, `tools/orchestrator_repair.py` and `tools/orchestrator_post_merge.py`. Missing, ambiguous, stale or cancelled evidence is non-green and fails closed.

## Bounded AI executor
`tools/orchestrator_executor.py` defines the pure request/result contract. `tools/orchestrator_executor_adapter.py` adds strict versioned envelopes and request digests. `tools/orchestrator_control_plane.py` binds invocation and result acceptance to the exact persisted Story, baseline and lifecycle state.

Executor invocation is allowed only in planning, implementation and bounded repair. A result cannot advance lifecycle state. Physical, secret and product-decision stops map through deterministic transitions to their explicit blocker states. Stale Story, baseline, state, request digest, budget escape, unknown fields and unauthorized output types fail closed.

Executor output is proposal data only. It cannot authorize merge, write directly to `main`, establish hardware verification, supply secrets, or approve destructive actions. Lifecycle transitions and privileged effects remain outside the executor.

## Merge authority
The read-only evidence gate acquires current PR/check/review facts. `tools/orchestrator_privileged_merge.py` is the final pure authorization policy immediately before mutation. It requires the persisted binding to match fresh PR Story/baseline/PR/HEAD evidence and exact required CI/security evidence. Ordinary solo-development changes do not fabricate self-approval; protected control-plane changes retain the external exact-HEAD security-review boundary.

`.github/workflows/orchestrator-v2-privileged-merge.yml` is intentionally narrow. It receives the already-persisted Story/baseline/PR/HEAD binding, re-fetches GitHub facts, evaluates deterministic authorization, re-fetches HEAD once more immediately before mutation, and invokes merge with the expected SHA.

Protected Orchestrator/workflow files require an approval bound to current HEAD in addition to required security CI. Any changed HEAD invalidates prior authorization. Generated agentic `.lock.yml` remains generated-only and is never manually edited.

## Hardware boundary
CI, mocks, simulation and AI claims are never `HARDWARE_VERIFIED`. Physical or destructive hardware actions require explicit operator authority and remain outside repository automation.

## Completion boundary
The Orchestrator v2 control-plane foundation is complete when state reconciliation, bounded repair, GitHub evidence, solo merge policy, privileged protected merge boundary, post-merge handoff, bounded executor envelopes and deterministic executor lifecycle integration are all covered by P0 tests. Provider-specific AI transport remains replaceable infrastructure rather than lifecycle authority.

## Invariants
INV-01 AI never writes directly to main. INV-02 AI never receives production secrets. INV-03 AI output is always untrusted. INV-04 merge decisions are deterministic. INV-05 approval is bound to exact SHA where required by protected policy. INV-06 control-plane/generated security files cannot silently auto-merge. INV-07 hardware verification requires physical evidence. INV-08 destructive hardware actions require explicit authority. INV-09 network access is deny-by-default where applicable. INV-10 critical dependencies require integrity verification. INV-11 autonomous loops are bounded. INV-12 transitions are validated. INV-13 stale executions cannot mutate current state. INV-14 ambiguity fails closed. INV-15 recovery does not require AI.
