# FPV Uhyliant autonomous development framework

Current `main` and canonical repository documents are the only project authority. Historical chat code must never replace newer repository state.

## Mandatory context
Before material work read `PRODUCT_UX.md`, `PROJECT_STATE.md`, `DEVELOPMENT_GUIDE.md`, `HARDWARE_E2E.md`, `DELIVERY_ROADMAP.md` and this file from current `main`.

## Autonomous operator contract
Development is software-first. Continue without intermediate questions whenever the next software action is derivable from repository state, tests, CI, sanitized evidence and the canonical roadmap. Physical OpenIPC acceptance is a separate final integration/release gate and does not block independent software-only work.

Stop only for `PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, `PRODUCT_DECISION_REQUIRED`, exhausted bounded automation/repair budget, or inconsistent/missing evidence that cannot be resolved safely.

Never infer physical success from CI, simulation, mocks, cached state or cloud metadata.

## Work selection
1. Refresh current `main` and inspect current CI.
2. Read and validate `PROJECT_STATE.json` and the canonical roadmap.
3. Select the explicit `nextSoftwareMilestone`; track `nextPhysicalMilestone` separately.
4. Find the largest incomplete dependency-valid software batch in that milestone.
5. Preserve product and safety invariants.
6. Repair the active batch before unrelated work if CI is red.
7. After a green authorized merge, refresh `main`, re-audit and continue without waiting for a manual "green" or "continue".
8. Do not stop merely because E0 physical evidence is deferred if independent software work remains.

## Git contract
Use `automation/<epic>-<short-purpose>` branches and reviewable PRs. Branch from current green `main`; keep one logically complete change per PR; update tests/docs with implementation; validate; publish a PR containing Story/Epic scope, tests and risks; repair the same PR on red CI. Autonomous workflows do not directly mutate `main`.

## Project state contract
Machine state must distinguish software readiness from physical acceptance and release blocking. `nextSoftwareMilestone` drives repository-only work. `nextPhysicalMilestone` records the deferred hardware gate. A null physical result never becomes success without observed evidence.

Project Doctor is software evidence only. It may validate schema, canonical drift, compile/tests and software readiness, but it cannot establish physical hardware acceptance.

## CI repair loop
On red CI identify the failing job/test/contract, compare it to the active diff and invariants, repair only the active batch and related regression coverage, rerun validation, and update the same PR. Never weaken a safety invariant or relabel missing physical evidence as success.

On green CI apply the existing review/merge authorization contract, merge only when authorized, refresh from new `main`, select the next dependency-valid software batch and continue.

## Agentic workflow security
Agentic workflows receive only necessary permissions. Prefer reviewable PRs/issues/comments over direct mutation. Secrets never enter prompts, evidence, logs, PR bodies or agent-visible repository files. Autonomous workflows never execute physical destructive firmware operations; those remain in the guarded local application with explicit operator confirmation.

## Current software-first order
1. Complete E8 controller onboarding software.
2. Complete E9 Diagnostics 2.0.
3. Complete E13 automated UI review harness.
4. Complete E14 video-first UX finalization.
5. Complete E15 software packaging/update/release readiness.
6. Advance E10/E11 and E12 in parallel whenever dependency-valid and not disruptive to the active critical software batch.
7. Prepare all safely testable E0/E1 workflow boundaries without claiming physical acceptance.
8. Near release, execute real E0/E1 physical validation, repair evidence-backed regressions, then pass the production release gate.

## Review output
Every autonomous PR states active Epic/Story scope, changes, why the batch is complete, tests/checks, CI status when known, remaining physical/secret/product blockers, and the exact next software step after merge.
