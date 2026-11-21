# FPV Uhyliant autonomous development framework

This contract makes repository development independent of chat history and of any particular AI assistant. Current `main` and the canonical repository documents are the only project authority.

## Mandatory context
Before material work, read from current `main`:
- `PRODUCT_UX.md`
- `PROJECT_STATE.md`
- `DEVELOPMENT_GUIDE.md`
- `HARDWARE_E2E.md`
- `DELIVERY_ROADMAP.md`
- this file

Never restore historical chat code over newer repository state.

## Autonomous operator contract
The development agent should continue without intermediate user questions whenever the next action can be determined from repository state, tests, CI, sanitized evidence, and the canonical roadmap.

Stop and request the user only for:
1. `PHYSICAL_ACTION_REQUIRED` - real hardware must be connected, power-cycled, observed, or otherwise manipulated.
2. `SECRET_REQUIRED` - a credential, secret or key must be entered outside the agent runtime.
3. `PRODUCT_DECISION_REQUIRED` - a genuine product/UX choice cannot be determined from the canonical plan.

Do not request confirmation for routine file edits, tests, refactors required by the active story, CI repairs, or documentation synchronization.

## Work selection
1. Read the current canonical delivery roadmap.
2. Find the earliest incomplete Epic/Story whose dependencies are satisfied.
3. Prefer the largest safe logically complete implementation batch within that ready scope.
4. Preserve all canonical safety and product invariants.
5. Do not begin unrelated work while the active batch is failing.

## Git contract
Normal autonomous development uses a work branch and reviewable pull request rather than unrestricted direct writes to `main`.

Branch naming:
`automation/<epic>-<short-purpose>`

A batch should:
1. branch from the current green `main`;
2. contain one logically complete change;
3. update related tests and canonical docs in the same batch when required;
4. run the required validation before publication;
5. publish a pull request with scope, tests, known risks and the roadmap Story IDs it closes;
6. wait for required CI checks;
7. repair the same branch/PR on red CI;
8. never start the next roadmap batch until the current one is green and merged.

Direct `main` mutation by an autonomous workflow is not part of this contract.

## CI repair loop
When CI is red:
1. identify the failing job, test and contract;
2. compare the failure with the active batch diff and canonical invariants;
3. decide whether production behavior or the test contract is wrong;
4. repair only the active batch and directly related regression coverage;
5. rerun validation;
6. update the same PR;
7. repeat until green or until a real external/physical/secret/product blocker is proven.

Never weaken a safety invariant merely to make CI green. Never hide, skip, or relabel a failing physical requirement as software success.

## Project Doctor interface
`tools/project_doctor.py` is the planned machine-readable readiness entry point. Until implemented, normal repository tests and canonical checks remain authoritative.

The target output contract is JSON:
```json
{
  "schemaVersion": 1,
  "status": "READY",
  "area": "repository",
  "stage": "validation",
  "reasonCode": "ready",
  "summary": "Repository validation passed",
  "checks": [],
  "nextMilestone": "E1"
}
```

Blocked form:
```json
{
  "schemaVersion": 1,
  "status": "BLOCKED",
  "area": "firmware",
  "stage": "artifact-integrity",
  "reasonCode": "sha-mismatch",
  "summary": "Firmware artifact integrity failed",
  "checks": [],
  "nextMilestone": null
}
```

Requirements:
- deterministic exit code: 0 for READY, non-zero for BLOCKED/internal failure;
- no secrets in output;
- reason codes stable enough for CI/agent consumption;
- human-readable summary included;
- no synthetic hardware success;
- canonical drift detectable when machine-readable project state is introduced.

## Agentic workflow security contract
Agentic workflows must be read-only by default and receive only the minimum permissions required for declared safe outputs. Prefer reviewable pull requests or issues/comments over direct repository mutation.

Secrets must not be placed in prompts, generated evidence, logs, pull-request bodies, or agent-visible repository files. Hardware credentials remain session-local to the desktop application.

Autonomous workflows must never perform physical destructive firmware execution. Hardware destructive actions remain inside the desktop application's guarded local workflow with explicit operator confirmation.

## Review output
Every autonomous PR should state:
- active Epic/Story IDs;
- what changed;
- why the batch is logically complete;
- tests/checks executed;
- CI status when known;
- remaining physical, secret or product-decision blockers;
- exact next roadmap step after merge.

The target user interaction is therefore limited to green/red CI evidence, physical actions, secret entry, and product judgement such as `подобається / не подобається`.
