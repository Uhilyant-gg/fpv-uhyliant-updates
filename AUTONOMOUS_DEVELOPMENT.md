# FPV Uhyliant autonomous development framework

Current `main` and canonical repository documents are the only project authority. Historical chat code must never replace newer repository state.

## Mandatory context
Before material work read `PRODUCT_UX.md`, `PROJECT_STATE.md`, `DEVELOPMENT_GUIDE.md`, `HARDWARE_E2E.md`, `DELIVERY_ROADMAP.md` and this file from current `main`.

## Autonomous operator contract
Continue without intermediate questions whenever the next action is derivable from repository state, tests, CI, sanitized evidence and the canonical roadmap. Stop only for `PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, or `PRODUCT_DECISION_REQUIRED`.

## Work selection
1. Read the current canonical roadmap.
2. Find the earliest incomplete Epic/Story whose dependencies are satisfied.
3. Prefer the largest safe logically complete batch in that scope.
4. Preserve all safety/product invariants.
5. Repair the active batch before unrelated work if CI is red.

## Git contract
Use `automation/<epic>-<short-purpose>` branches and reviewable PRs. Branch from current green `main`; keep one logically complete change; update tests/docs with the implementation; validate; publish a PR containing Story IDs, scope, tests and risks; repair the same PR on red CI; do not start the next roadmap batch before the current one is green and merged. Autonomous workflows do not directly mutate `main`.

## Project Doctor interface
`tools/project_doctor.py` is implemented. It emits deterministic JSON, verifies canonical-file presence, compiles Python sources, runs application tests and tool tests, and exits zero only for READY. Its output must never be interpreted as physical hardware validation.

The current implementation is an E5 foundation, not E5 completion. Remaining E5 contract includes a canonical machine-readable project-state/capability matrix, canonical drift/consistency validation, CI integration, and an audited next-milestone value derived from that state rather than a stale hard-coded phase.

Target fields remain: `schemaVersion`, `status`, `area`, `stage`, `reasonCode`, `summary`, `checks`, `nextMilestone`. Requirements remain deterministic exit behavior, no secret output, stable reason codes, human-readable summary, no synthetic hardware success and detectable canonical drift.

## CI repair loop
On red CI identify the failing job/test/contract, compare it to the active diff and invariants, repair only the active batch and related regression coverage, rerun validation, and update the same PR. Never weaken a safety invariant or relabel missing physical evidence as success.

## Agentic workflow security
Agentic workflows are read-only by default and receive minimum permissions. Prefer reviewable PRs/issues/comments over direct mutation. Secrets never enter prompts, evidence, logs, PR bodies or agent-visible repository files. Autonomous workflows never execute physical destructive firmware operations; those remain in the guarded local application with explicit operator confirmation.

## Review output
Every autonomous PR states active Epic/Story IDs, changes, why the batch is complete, tests/checks, CI status when known, remaining physical/secret/product blockers, and exact next roadmap step after merge.