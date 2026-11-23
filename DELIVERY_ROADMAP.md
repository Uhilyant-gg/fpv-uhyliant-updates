# FPV Uhyliant canonical delivery roadmap

This file is the durable implementation plan for FPV Uhyliant. Current `main` plus the canonical documents are authoritative.

## Operating model
Development is autonomous by default. Human participation is reserved for physical hardware actions, secrets/credentials/keys, and genuine product decisions.

Continuous loop: `current main -> largest safe logically complete batch -> tests -> reviewable PR -> CI -> repair on red / gated merge on green -> refresh main -> replan -> next dependency-valid batch`.

A green, safely mergeable batch must not require an intermediate human "continue" or "green" command. After merge, refresh from the new `main` and continue automatically while the next action is deterministically supported by repository state and evidence.

Never treat software CI as physical hardware evidence. Never start unrelated work on a red baseline. Stop the continuous loop only for a physical action, secret/credential/key, genuine product decision, exhausted bounded automation/repair budget, or inconsistent/missing evidence that cannot be resolved safely.

## Current audited state
Physical E0 remains incomplete and deferred until real OpenIPC evidence is captured. Software validation never closes that gate.

E5 - Project Doctor and Machine-Readable Project State is complete at the repository-software boundary: canonical machine-readable state, capability validation, deterministic repository-only next-milestone derivation, drift detection, CI execution through Project Doctor, and fail-closed regression coverage are present. This completion does not imply physical Hardware E2E success.

The next repository-only milestone selected by the canonical capability matrix is E2, while E0 remains the physical critical-path gate.

## Progress model
Progress is reported in two layers so existing foundations are not confused with roadmap completion:

- **Roadmap completion:** an Epic/Story is complete only when its acceptance criteria have repository or physical evidence.
- **Engineering readiness:** existing foundations may materially support a future Story while it remains incomplete.

The canonical planning estimate remains **35%** until a broader acceptance-based re-audit changes it. Do not mechanically increase this percentage for commits.

## Delivery order and status

### E0 - Physical OpenIPC Hardware E2E | BLOCKED ON PHYSICAL EVIDENCE
Stories: E0-S1..E0-S6.

Acceptance: real OpenIPC camera; observed platform/sensor; verified bound artifact/preflight; session credentials and explicit host-key acceptance; deliberate guarded update; reboot-pending; bounded rediscovery; matching hardware continuity; non-empty observed post-update firmware; preserved sanitized preflight and terminal evidence.

Next action: execute the current provenance-validated Hardware E2E artifact against real hardware. If it fails, repair only the evidence-backed blocker and repeat.

### E1 - Automated Hardware Validation | READY AFTER E0
Stories E1-S1..E1-S10: deterministic validation model; discovery/device selection; identity observation; firmware acquisition; immutable transaction; credential/host-key gates; explicit destructive confirmation; reboot/rediscovery/post-update verification; staged evidence/reason codes; compact guided validation UI.

### E2 - Unified Health and Evidence Contract | NEXT REPOSITORY-ONLY MILESTONE
Stories E2-S1..E2-S7. Common schema must expose state, health, summary, reasonCode, evidence and safeActions. User health vocabulary is only ready / attention / problem / unknown. Unknown never becomes ready without evidence.

### E3 - Next Best Action Engine | PENDING, depends on E2
Stories E3-S1..E3-S6. Deterministic priority model with at most one primary normal-workflow action; safety gates remain authoritative.

### E4 - Zero-Config Startup and Restore | PENDING, depends on E2/E3
Stories E4-S1..E4-S7. Target: `launch -> restore/discover -> verified usable camera -> video`; manual IP is fallback; ambiguity is never guessed.

### E5 - Project Doctor and Machine-Readable Project State | COMPLETE
Completed repository-software contract: canonical machine-readable project state and capability matrix; schema/status validation; deterministic next-milestone derivation; canonical hardware-boundary drift checks; Project Doctor integration in repository CI; fail-closed regression coverage. Project Doctor remains software evidence only and can never establish physical E0 completion.

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
Physical critical path: `E0 -> E1`.

Product path after the physical gate: `E1 -> E2 -> E3 -> E4 -> E9 -> E14 -> E15`.

Enabling path: `E5 -> E2 -> E6 -> E7 -> E15`, subject to each Epic's stated dependencies.

Other dependencies: E8 depends on E2/E3 and feeds E14; E10 depends on E2/E4; E11 depends on E10 and feeds E14; E12 depends on E9 and feeds E14; E13 depends on E2/E3 and supports E14.

## Next largest safe batch
**Physical boundary:** E0 still requires operator-controlled real-hardware validation.

**Repository-only boundary:** E5 is complete. The canonical capability matrix selects E2 as the next software milestone. Work there must preserve the fact that E1 has not been physically accepted and must not manufacture E1/E0 evidence. If an E2 slice requires accepted E1 physical evidence rather than merely a presentation contract, stop at that dependency instead of guessing.

## Handoff rule
At each session start and after each successful merge:
1. Read/refresh current `main` and canonical state relevant to the next decision.
2. Run/inspect Project Doctor and current CI evidence when available.
3. Validate `PROJECT_STATE.json` and use its deterministic repository-only `nextMilestone`.
4. Determine the earliest incomplete Story in that milestone whose dependencies are actually satisfied.
5. Prefer the largest safe logically complete batch.
6. Never restore historical chat code over current repository state.
7. Stop only for physical hardware, secrets/credentials/keys, a genuine product decision, exhausted bounded automation, or unresolved inconsistent evidence.
8. After one implementation commit, publish/refresh its reviewable PR and observe CI. Repair the same batch on red. On green, pass the existing merge gates, merge when authorized, refresh `main`, and continue automatically with the next dependency-valid batch.
