# FPV Uhyliant canonical delivery roadmap

This file is the durable implementation plan for FPV Uhyliant. Current `main` plus the canonical documents are authoritative.

## Operating model
Development is autonomous by default. Human participation is reserved for physical hardware actions, secrets/credentials/keys, and genuine product decisions.

Strict loop: `current main -> largest safe logically complete batch -> tests -> one commit -> CI -> stop`.

Never treat software CI as physical hardware evidence. Never start unrelated work on a red baseline.

## Audited baseline
Audit baseline: `main` at `88c90461ffef08d840965361cbbe9c3a45ff0434`.

The repository already contains substantial foundations that predate this roadmap: route-aware camera discovery, OpenIPC identity and firmware acquisition, guarded authenticated upgrade transport, reboot rediscovery/post-flash verification, staged diagnostics, telemetry/video runtimes, Windows updater/rollback/startup acknowledgement, Hardware E2E runtime/UI and extensive regression tests. These foundations reduce implementation risk but do not close a roadmap Story unless that Story's acceptance contract is satisfied.

`tools/project_doctor.py` is implemented and currently checks canonical-file presence, Python compilation, application tests and tool tests. Therefore the older statement that Project Doctor is only planned is stale. E5 remains **partial** because a canonical machine-readable capability matrix/state schema, canonical drift checks and CI integration are not yet established.

No common Unified Health/Evidence contract or Next Best Action engine is present on this audited baseline. E2 and E3 therefore remain pending even though subsystem-specific states already exist.

The physical E0 gate remains the first critical-path gate until repository evidence records a complete real-camera lifecycle. Software tests and the Hardware E2E harness do not close E0.

## Progress model
Progress is reported in two layers so existing foundations are not confused with roadmap completion:

- **Roadmap completion:** an Epic/Story is complete only when its acceptance criteria have repository or physical evidence.
- **Engineering readiness:** existing foundations may materially support a future Story while it remains incomplete.

At this baseline the defensible project-level planning estimate is **about 35% engineering-complete, with roughly 65% remaining**. This is an engineering estimate, not a count of green tests or closed Stories. The largest uncertainty is product integration after Hardware E2E: unified health, NBA, zero-config startup, controllers, accounts/sharing, Diagnostics 2.0, AI assistance, final video-first UX and production release gating remain roadmap work.

Do not mechanically increase this percentage for commits. Re-audit against acceptance criteria and physical evidence.

## Delivery order and status

### E0 - Physical OpenIPC Hardware E2E | BLOCKED ON PHYSICAL EVIDENCE
Stories: E0-S1..E0-S6.

Acceptance: real OpenIPC camera; observed platform/sensor; verified bound artifact/preflight; session credentials and explicit host-key acceptance; deliberate guarded update; reboot-pending; bounded rediscovery; matching hardware continuity; non-empty observed post-update firmware; preserved sanitized preflight and terminal evidence.

Next action: execute the current provenance-validated Hardware E2E artifact against real hardware. If it fails, repair only the evidence-backed blocker and repeat.

### E1 - Automated Hardware Validation | READY AFTER E0
Stories E1-S1..E1-S10: deterministic validation model; discovery/device selection; identity observation; firmware acquisition; immutable transaction; credential/host-key gates; explicit destructive confirmation; reboot/rediscovery/post-update verification; staged evidence/reason codes; compact guided validation UI.

### E2 - Unified Health and Evidence Contract | PENDING, depends on E1
Stories E2-S1..E2-S7. Common schema must expose state, health, summary, reasonCode, evidence and safeActions. User health vocabulary is only ready / attention / problem / unknown. Unknown never becomes ready without evidence.

### E3 - Next Best Action Engine | PENDING, depends on E2
Stories E3-S1..E3-S6. Deterministic priority model with at most one primary normal-workflow action; safety gates remain authoritative.

### E4 - Zero-Config Startup and Restore | PENDING, depends on E2/E3
Stories E4-S1..E4-S7. Target: `launch -> restore/discover -> verified usable camera -> video`; manual IP is fallback; ambiguity is never guessed.

### E5 - Project Doctor and Machine-Readable Project State | PARTIAL, depends on E2 for final contract
Implemented: deterministic JSON readiness entry point, canonical-file check, compile/app/tool test orchestration, READY/BLOCKED exit behavior.
Remaining: E5-S1 machine-readable canonical project-state schema; E5-S2 capability matrix; E5-S3 canonical consistency/drift checks; E5-S6 CI integration, plus alignment of `nextMilestone` with the audited state.

### E6 - Hardware Simulator and Fault Injection | PENDING, depends on E1/E2
Stories E6-S1..E6-S7. Simulate OpenIPC identity/update/reboot/DHCP/multi-device behavior and required failure modes. Simulator evidence can never be labeled physical validation.

### E7 - Scenario-Driven CI | PENDING, depends on E5/E6
Stories E7-S1..E7-S7. Behavioral startup, discovery/video, firmware, recovery and later controller scenarios with machine-readable failure summaries.

### E8 - FPV/RC Controller Onboarding | PENDING, depends on E2/E3
Stories E8-S1..E8-S9. Automatic detection/restore, observed inputs, calibration/mapping, safe profile persistence, unified health, Advanced-only manual transport.

### E9 - Diagnostics 2.0 | PENDING, depends on E2/E3
Stories E9-S1..E9-S8. Common findings/reason codes, automated evidence, deterministic non-destructive remediation and revalidation, sanitized support bundle, progressive disclosure, NBA integration.

### E10 - Accounts and Synchronized Device Registry | PENDING, depends on E2/E4
Stories E10-S1..E10-S8. Account remains optional for local FPV; cloud metadata never substitutes for fresh local observation.

### E11 - Device Sharing and Ownership Transfer | PENDING, depends on E10
Stories E11-S1..E11-S7. Explicit least-privilege sharing, revocation and deliberate ownership transfer without sharing credentials or bypassing local safety gates.

### E12 - AI Diagnostic Assistant | PENDING, depends on E9
Stories E12-S1..E12-S8. Sanitized structured evidence only; advisory explanations/actions only; no authority over identity, compatibility, ownership, firmware success or destructive operations.

### E13 - Automated UI Review Harness | PENDING, depends on E2/E3
Stories E13-S1..E13-S7. Deterministic UI fixtures, render/startup harness, canonical states, screenshots/review artifacts and CI smoke validation.

### E14 - Video-First UX Finalization | PENDING, depends on E3/E4/E8/E9
Stories E14-S1..E14-S9. Video gets largest practical area; remove duplicated/dead normal workflows; integrate health/NBA/controller/diagnostics/account/AI contextually; finalize Advanced vs Service Mode and responsive polish.

### E15 - Release, Installer and OTA Production Readiness | PENDING, depends on E14; E7 strongly preferred
Stories E15-S1..E15-S9. Production packages, installer layout, signed manifest/package integrity, OTA, startup acknowledgement, atomic rollback, packaged smoke, provenance and production release gate.

## Dependency graph
Critical path: `E0 -> E1 -> E2 -> E3 -> E4 -> E9 -> E14 -> E15`.

Enabling path: `E2 -> E5 -> E6 -> E7 -> E15`.

Other dependencies: E8 depends on E2/E3 and feeds E14; E10 depends on E2/E4; E11 depends on E10 and feeds E14; E12 depends on E9 and feeds E14; E13 depends on E2/E3 and supports E14.

## Next largest safe batch
**Current boundary: E0 physical validation.** Repository-only product work must not pretend this gate is complete.

If E0 physical evidence is already available outside the repository, preserve/import its sanitized result before advancing. Otherwise the next repository implementation batch after that hardware gate is **E1 automated validation**, preferably as one substantial vertical slice covering the pure state contract through non-destructive orchestration and regression tests before UI polish.

While E0 awaits physical/operator input, only non-conflicting enabling maintenance may proceed. Do not advance E2/E3 as though E1 were accepted.

## Handoff rule
At each session start:
1. Read current `main` and all canonical documents.
2. Run/inspect Project Doctor and current CI evidence when available.
3. Determine the earliest incomplete Story whose dependencies are satisfied.
4. Prefer the largest safe logically complete batch.
5. Never restore historical chat code over current repository state.
6. Stop only for physical hardware, secrets/credentials/keys, or a genuine product decision.
7. After one implementation commit, stop for CI; repair the same batch on red.