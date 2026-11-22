# Orchestrator v2

Orchestrator v2 keeps lifecycle authority in a deterministic control plane. AI proposes; deterministic policy decides; GitHub enforces. AI is replaceable and untrusted.

## Lifecycle
Roadmap -> Story -> implementation -> tests -> PR -> CI -> bounded repair -> security/review gate -> merge -> project-state update -> next Story. Privileged execution is always bound to Story, baseline SHA, PR and expected HEAD SHA.

Persisted strict state, factual GitHub evidence normalization and bounded repair are implemented in `tools/orchestrator_state.py`, `tools/orchestrator_github_evidence.py` and `tools/orchestrator_repair.py`. Missing, ambiguous, stale or cancelled evidence is non-green and fails closed.

## Merge authority
The read-only evidence gate acquires current PR/check/review facts. `tools/orchestrator_privileged_merge.py` is the final pure authorization policy immediately before mutation. It requires the persisted binding to match fresh PR Story/baseline/PR/HEAD evidence and reuses exact required-CI/security/review/tested-SHA policy.

`.github/workflows/orchestrator-v2-privileged-merge.yml` is intentionally narrow. It is manual-dispatch only in this phase, receives the already-persisted Story/baseline/PR/HEAD binding, checks out the exact expected HEAD without persisted credentials, re-fetches GitHub facts, evaluates deterministic authorization, re-fetches HEAD once more immediately before mutation, and calls the GitHub merge API with that expected SHA.

The privileged workflow has write permission only because GitHub merge is its sole terminal effect. It uses the protected `orchestrator-merge` environment so repository environment protection can require security authority outside AI. AI does not decide whether this environment is approved.

Protected Orchestrator/workflow files require an approval bound to current HEAD in addition to required security CI. Any changed HEAD invalidates prior authorization. Generated agentic `.lock.yml` remains generated-only and is never manually edited.

## Hardware boundary
CI, mocks, simulation and AI claims are never `HARDWARE_VERIFIED`. Physical or destructive hardware actions require explicit operator authority and remain outside repository automation.

## Invariants
INV-01 AI never writes directly to main. INV-02 AI never receives production secrets. INV-03 AI output is always untrusted. INV-04 merge decisions are deterministic. INV-05 approval is bound to exact SHA. INV-06 control-plane/generated security files cannot silently auto-merge. INV-07 hardware verification requires physical evidence. INV-08 destructive hardware actions require explicit authority. INV-09 network access is deny-by-default where applicable. INV-10 critical dependencies require integrity verification. INV-11 autonomous loops are bounded. INV-12 transitions are validated. INV-13 stale executions cannot mutate current state. INV-14 ambiguity fails closed. INV-15 recovery does not require AI.
