# FPV Uhyliant canonical delivery roadmap

Current `main` plus the canonical documents are authoritative.

## Delivery policy
Development is **software-first**. Physical OpenIPC acceptance remains mandatory, but it is intentionally deferred to the final integration/release stage so it does not block independent software work.

Continuous loop:

`current main -> largest dependency-valid software batch -> focused tests -> PR -> CI -> repair red -> gated merge -> refresh main -> replan -> next software batch`

Physical loop, executed near release:

`software-ready candidate -> real OpenIPC E0 -> E1 guided validation -> physical regressions -> repair/retest -> production release gate`

Never treat simulator, CI, mocks, cached state or cloud metadata as physical evidence. Hardware absence may block a physical acceptance claim, but must not block unrelated software-only work.

## Current audited state
- E2-E7 are complete at the repository-software boundary.
- E8 controller profile core landed in #149: validated calibration, explicit four-axis mapping, normalized controls, fail-closed profile application and identity-bound restore.
- E8 remains incomplete: local discovery/live-input acquisition, durable non-secret profile persistence, unified controller health wiring and onboarding UI remain.
- E9-E15 are not complete; several have useful foundations and remain eligible when dependencies are satisfied.
- E0 is physically incomplete and deliberately deferred to final integration. Its acceptance criteria are unchanged.

Roadmap completion remains **38%** until additional Epic acceptance contracts are actually satisfied. Partial foundations do not count as complete Epics.

## Software-first execution order

### Phase A - E8 FPV/RC Controller Onboarding | IN PROGRESS
Dependencies E2/E3 are complete.

Deliver in reviewable batches:
1. durable versioned non-secret controller profile persistence with atomic/fail-closed load and migration tests;
2. bounded local controller discovery and live-input acquisition with deterministic fake provider coverage;
3. controller health and Next Best Action integration for missing/stale/invalid/mismatched states;
4. task-oriented onboarding UI for observed inputs, calibration, mapping and restore, with manual transport only in Advanced.

Physical presence and live input remain locally observed; software fixtures never satisfy physical acceptance.

### Phase B - E9 Diagnostics 2.0 | PENDING, depends on E2/E3
Complete the existing diagnostics foundations into common findings/reason codes, automated evidence collection, deterministic non-destructive remediation with revalidation, sanitized support bundles, progressive disclosure and NBA integration.

### Phase C - E13 Automated UI Review Harness | PENDING, depends on E2/E3
Build deterministic UI fixtures, canonical state rendering, startup/render smoke tests, screenshot/review artifacts and Windows/QML CI validation. This phase precedes final UX cleanup so visual regressions become observable.

### Phase D - E14 Video-First UX Finalization | PENDING, depends on E3/E4/E8/E9
Make the video workspace the dominant operational surface, integrate controller/health/NBA/diagnostics contextually, remove duplicated normal workflows, finalize Advanced versus Service Mode and responsive/navigation polish.

### Phase E - E15 Release, Installer and OTA Software Readiness | PENDING, depends on E14
Complete deterministic packaging, installer layout, manifest/integrity verification, update staging, startup acknowledgement, atomic rollback, packaged smoke tests, provenance and release evidence. Real signing credentials and final physical acceptance remain gated.

### Parallel dependency-valid track
- E10 Accounts and Synchronized Device Registry depends on E2/E4. Keep local FPV fully usable without Internet/account service.
- E11 Device Sharing and Ownership Transfer follows E10 with explicit least privilege and no credential sharing.
- E12 AI Diagnostic Assistant follows E9 and consumes sanitized structured evidence only; it is advisory and never safety authority.

These tracks may proceed when their dependencies are met, but must not displace a higher-value active batch with failing CI.

## Final physical integration and release gate

### E0 - Physical OpenIPC Hardware E2E | DEFERRED, RELEASE-BLOCKING
Physical acceptance is intentionally postponed, not waived. Final evidence still requires a real OpenIPC camera, observed platform/sensor, verified bound artifact/preflight, session credentials and explicit host-key acceptance, deliberate guarded update, reboot-pending, bounded rediscovery, matching hardware continuity, observed post-update firmware and sanitized staged evidence.

### E1 - Automated Hardware Validation | FINAL INTEGRATION AFTER E0 SOFTWARE PREP
Before hardware is available, implement all safely testable workflow/model/UI/provider boundaries using deterministic fixtures. Final acceptance still requires real hardware evidence and must fail closed when evidence is absent.

No production-ready claim may bypass E0/E1 physical acceptance.

## Canonical dependency model
Software primary path:

`E8 -> E9 -> E13 -> E14 -> E15 software-ready`

Parallel path:

`E10 -> E11`, and `E9 -> E12`

Final release gate:

`software-ready candidate -> E0 physical acceptance -> E1 integrated validation -> E15 production release`

Existing completed enabling base:

`E2 + E3 + E4 + E5 + E6 + E7`

## Next largest safe batch
**E8 profile persistence** is the next bounded software-only batch: introduce durable versioned non-secret controller profile storage with atomic/fail-closed behavior and focused tests. After merge, refresh `main` and re-audit E8 before selecting discovery/live-input work.

## Handoff rule
1. Refresh current `main` and inspect current CI before material work.
2. Validate canonical state and preserve all safety invariants.
3. Select `nextSoftwareMilestone` independently from `nextPhysicalMilestone`.
4. Choose the largest dependency-valid software-only batch that can be reviewed and validated coherently.
5. Repair the active PR on red before unrelated work.
6. On green and authorized merge, refresh `main` and continue automatically.
7. Stop only for a required physical action, secret/credential/key, genuine product decision, exhausted bounded automation, or unresolved evidence inconsistency.
8. Deferring physical acceptance never permits claiming physical success or production readiness.
