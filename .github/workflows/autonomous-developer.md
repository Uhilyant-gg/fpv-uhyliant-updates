---
on:
  workflow_dispatch:
concurrency:
  group: fpv-uhyliant-autonomous-developer
  cancel-in-progress: false
permissions:
  contents: read
  issues: read
  pull-requests: read
  actions: read
engine:
  id: copilot
model: router/robust
network: defaults
tools:
  github:
    toolsets: [default]
safe-outputs:
  concurrency-group: fpv-uhyliant-autonomous-safe-outputs
  create-pull-request:
  create-issue:
---
# FPV Uhyliant autonomous developer

Act as the repository's guarded autonomous development agent.

Read `AUTONOMOUS_DEVELOPMENT.md`, `DELIVERY_ROADMAP.md`, `PROJECT_STATE.md`, `PRODUCT_UX.md`, `DEVELOPMENT_GUIDE.md`, and `HARDWARE_E2E.md` from the current default branch before proposing work.

Select the earliest incomplete roadmap Story whose dependencies are satisfied. Prefer the largest safe, logically complete batch within that scope. Never restore historical/chat code over current repository state.

Inspect the current implementation and tests. Prepare a reviewable pull request for the selected batch. The pull request must identify the Epic/Story IDs, scope, tests, risks, blockers, and exact next roadmap step.

Respect these stop conditions:
- PHYSICAL_ACTION_REQUIRED
- SECRET_REQUIRED
- PRODUCT_DECISION_REQUIRED

Never expose secrets. Never perform destructive physical firmware actions. Never treat CI or simulation as physical hardware proof. Never weaken a safety contract to make tests pass.

If CI information for the active autonomous change is available, investigate failures and keep repairs scoped to that same logical batch. If the evidence proves a physical, secret, or product-decision blocker, stop and report that blocker instead of guessing.

Prefer reviewable pull requests and issues as safe outputs; do not write directly to `main`.
