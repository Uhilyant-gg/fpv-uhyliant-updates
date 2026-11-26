# FPV Uhyliant autonomous development framework

Current `main`, `PRODUCT_UX.md`, `PROJECT_STATE.md`, `PROJECT_STATE.json` and `DELIVERY_ROADMAP.md` are the project authority. Historical chat code must never replace newer repository state.

## Mandatory context
Before material work, read the current product constitution, project state, delivery roadmap, development guide and hardware E2E contract.

## Autonomous iteration contract
Every iteration must:
1. refresh and audit current `main` and active CI;
2. identify the largest verified user pain or release risk;
3. measure the candidate change against User Effort Score;
4. select the smallest safe logically complete vertical slice with the highest user value;
5. update implementation, tests and canonical documentation together;
6. publish or refresh one reviewable PR;
7. repair red CI on the same batch before unrelated work;
8. after authorized green merge, refresh `main`, re-audit and continue.

Do not select work primarily by feature count. Prefer simplification, automation, clarity, recovery and stability.

## Work selection order
1. Broken baseline or active red PR.
2. Safety, secret or data-loss regression.
3. Broken integrated first-run journey.
4. Failure to show understandable health within the defined 10-second target.
5. Manual configuration required in a normal path.
6. Raw technical language or missing recovery action.
7. Missing device discovery, Device Center, Timeline, backup or Next Best Action integration.
8. Physical acceptance required for a hardware claim or production gate.
9. Only then additional capability.

Physical validation may proceed in parallel when hardware and operator action are available. Its absence never permits a physical success claim. It also must not block independent software UX work that does not make such a claim.

## Stop conditions
Continue without intermediate questions when the next action is deterministic and safe. Stop only for:
- `PHYSICAL_ACTION_REQUIRED`;
- `SECRET_REQUIRED`;
- `PRODUCT_DECISION_REQUIRED`;
- exhausted bounded repair/automation budget;
- inconsistent or missing evidence that cannot be resolved safely.

## Git and CI contract
Use `automation/<epic>-<short-purpose>` branches created from current green `main`. Keep one coherent vertical slice per PR. Include scope, user pain, User Effort impact, tests, safety considerations, evidence, remaining blockers and exact next action.

Never weaken safety or acceptance tests to obtain green. Never start unrelated work on a red baseline. Autonomous workflows do not directly mutate `main`.

## Evidence discipline
Distinguish explicitly:
- implemented;
- covered by software tests;
- validated in packaged application;
- physically validated;
- production accepted.

Software CI, simulation, mocks, cached state and cloud metadata never become physical evidence. Unknown remains unknown.

## Product review gate
Every PR must answer:
1. Which user pain is reduced?
2. Which clicks, time, manual inputs or documentation steps are removed?
3. What is automated?
4. What normal-path technical detail is hidden?
5. What human-language message and recovery action are shown on failure?
6. How is success evidenced?
7. Does the change preserve the first-run acceptance contract?

If these questions have no meaningful answer, lower the priority or classify the change as infrastructure with an explicit product dependency.

## Project Doctor
Project Doctor validates repository consistency, canonical state, source compilation and tests. Its result is software evidence only. It cannot establish physical hardware acceptance or production readiness by itself.

## Review output
Report each line with:
- status: done, active, blocked or next;
- evidence;
- user impact;
- completion percentage only when the denominator and criteria are explicit;
- blocker;
- next safest action.

Do not report vague progress unsupported by commits, PRs, CI, packaged artifacts or observed hardware evidence.