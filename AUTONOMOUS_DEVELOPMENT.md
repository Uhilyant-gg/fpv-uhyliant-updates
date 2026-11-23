# FPV Uhyliant autonomous development framework

Current `main` and canonical repository documents are the only project authority. Historical chat code must never replace newer repository state.

## Mandatory context
Before material work read `PRODUCT_UX.md`, `PROJECT_STATE.md`, `DEVELOPMENT_GUIDE.md`, `HARDWARE_E2E.md`, `DELIVERY_ROADMAP.md` and this file from current `main`.

## Autonomous operator contract
Continue without intermediate questions whenever the next action is derivable from repository state, tests, CI, sanitized evidence and the canonical roadmap. Stop only for `PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, or `PRODUCT_DECISION_REQUIRED`.

## Work selection
1. Read the current canonical roadmap and `PROJECT_STATE.json`.
2. Validate canonical state before selecting work.
3. Use the deterministic `nextMilestone` derived from the capability matrix for repository-only enabling work; never use it to claim that deferred physical validation is complete.
4. Find the earliest incomplete Story in that milestone whose dependencies are satisfied.
5. Prefer the largest safe logically complete batch in that scope.
6. Preserve all safety/product invariants.
7. Repair the active batch before unrelated work if CI is red.

## Git contract
Use `automation/<epic>-<short-purpose>` branches and reviewable PRs. Branch from current green `main`; keep one logically complete change; update tests/docs with the implementation; validate; publish a PR containing Story IDs, scope, tests and risks; repair the same PR on red CI; do not start the next roadmap batch before the current one is green and merged. Autonomous workflows do not directly mutate `main`.

## Project Doctor interface
`tools/project_doctor.py` is implemented. It emits deterministic JSON, verifies canonical-file presence and machine-readable project state, rejects canonical drift, compiles Python sources, runs application tests and tool tests, and exits zero only for READY. Its output must never be interpreted as physical hardware validation.

`tools/project_state.py` owns validation of the canonical machine-readable state and derives the repository-only `nextMilestone` from the capability matrix. A stale recorded milestone, an unknown capability/status, impossible physical-evidence state, or canonical hardware-boundary drift fails closed.

Target Project Doctor fields are: `schemaVersion`, `status`, `area`, `stage`, `reasonCode`, `summary`, `checks`, `nextMilestone`. Requirements remain deterministic exit behavior, no secret output, stable reason codes, human-readable summary, no synthetic hardware success and detectable canonical drift.

## CI repair loop
On red CI identify the failing job/test/contract, compare it to the active diff and invariants, repair only the active batch and related regression coverage, rerun validation, and update the same PR. Never weaken a safety invariant or relabel missing physical evidence as success.

## Agentic workflow security
Agentic workflows are read-only by default and receive minimum permissions. Prefer reviewable PRs/issues/comments over direct mutation. Secrets never enter prompts, evidence, logs, PR bodies or agent-visible repository files. Autonomous workflows never execute physical destructive firmware operations; those remain in the guarded local application with explicit operator confirmation.

## Review output
Every autonomous PR states active Epic/Story IDs, changes, why the batch is complete, tests/checks, CI status when known, remaining physical/secret/product blockers, and exact next roadmap step after merge.
