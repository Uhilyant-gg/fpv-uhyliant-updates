# Orchestrator v2

Orchestrator v2 keeps lifecycle authority in a deterministic control plane. AI proposes; deterministic policy decides; GitHub enforces. AI is replaceable and untrusted.

## Lifecycle and state
Roadmap -> Story -> implementation -> tests -> PR -> CI -> bounded repair -> security/review gate -> merge -> project-state update -> next Story. State remains minimal and allowlisted. Privileged execution is bound to Story, baseline SHA, PR and expected HEAD SHA.

`tools/orchestrator_state.py` persists strict versioned state atomically. `tools/orchestrator_github_evidence.py` normalizes factual PR/check/review data without guessing missing evidence. `tools/orchestrator_repair.py` permits bounded repair only inside the same bound execution.

## GitHub evidence acquisition and merge authority
`.github/workflows/orchestrator-v2-merge-gate.yml` is a read-only GitHub evidence acquisition adapter. It fetches the PR, check runs for the observed HEAD and PR reviews using the GitHub API, then passes reduced JSON evidence to `tools/orchestrator_merge_gate.py`.

The adapter has only `contents: read`, `checks: read` and `pull-requests: read`. It deliberately cannot merge or write repository contents. A positive result is evidence that the deterministic policy considers this observed SHA eligible; it is not itself merge execution.

The gate requires explicit required-check and security-check names. Missing, failed, cancelled, duplicate or ambiguous checks fail closed. A cancelled run is non-green infrastructure evidence, not a test failure and not repair authority. Tested SHA and approved review commit must equal the observed current PR HEAD. A stale expected HEAD is denied before merge policy evaluation.

For normal automatic runs the workflow uses a stable PR-derived Story placeholder until canonical Story identity is supplied by the persisted Orchestrator execution. Manual dispatch accepts the active Story ID explicitly. This placeholder is not authority to cross Story boundaries; actual privileged merge execution must use persisted Story binding.

## Merge execution boundary
This batch intentionally stops before granting `contents: write`. The eventual merge actor must re-fetch current GitHub evidence immediately before merge, require exact persisted Story/baseline/PR/HEAD binding and required branch/security/review policy, and invoke GitHub merge with expected HEAD SHA. Any mismatch becomes stale/inconsistent and fails closed.

## Workflow integrity and hardware
Canonical/control-plane files and `.github/workflows/**` remain protected security scope. Agentic `.md` remains canonical and generated `.lock.yml` is never hand-edited. Existing gh-aw stale-lock/pinned-runtime machinery is reused. CI, mocks, simulation and AI claims are never `HARDWARE_VERIFIED`; destructive hardware work requires explicit authority.

## Security invariants
INV-01 AI never writes directly to main. INV-02 AI never receives production secrets. INV-03 AI output is always untrusted. INV-04 merge decisions are deterministic. INV-05 approval is bound to exact SHA. INV-06 control-plane/generated security files cannot silently auto-merge. INV-07 hardware verification requires physical evidence. INV-08 destructive hardware actions require explicit authority. INV-09 network access is deny-by-default where applicable. INV-10 critical dependencies require integrity verification. INV-11 autonomous loops are bounded. INV-12 transitions are validated. INV-13 stale executions cannot mutate current state. INV-14 ambiguity fails closed. INV-15 recovery does not require AI.
