# FPV Uhyliant canonical delivery roadmap

Current `main` plus the canonical documents are authoritative. This roadmap is ordered by user value, dependency and evidence, not by feature count.

## Delivery policy
The product is UX-first, automation-first and zero-config-first. Safety invariants remain authoritative.

Continuous loop:

`audit current main -> largest verified user pain -> smallest high-value vertical slice -> tests -> reviewable PR -> repair red / authorized merge green -> refresh main -> re-audit`

Never treat software CI as physical hardware evidence. Never allow a deferred physical step to justify a physical success claim. Independent software UX work may continue while physical validation awaits hardware or operator action.

## Current audited state
- Roadmap completion remains 38% under the existing acceptance model.
- E2 Unified Health, E3 Next Best Action, E4 Zero-Config Startup, E5 Project Doctor, E6 Hardware Simulator and E7 Scenario-Driven CI are complete at the repository-software boundary.
- E0 real OpenIPC Hardware E2E remains physically incomplete.
- E8 controller calibration/mapping/profile core exists, but controller discovery, live acquisition, durable persistence and onboarding remain incomplete.
- The largest product risk is not a missing subsystem. It is the absence of one evidenced integrated first-run journey that proves the user can launch, understand state, see devices and receive a useful next action without documentation or configuration editing.

## P0: Integrated user journey
### P0.1 First-Run Acceptance Harness | NEXT
Create one deterministic integrated contract for:

`install/start -> launch -> discovery/restore -> health -> devices -> next action -> usable operation`

Acceptance:
- defined measurement starts at application launch;
- understandable state appears in less than 10 seconds under declared fixture and packaged-test conditions;
- no terminal or configuration editing;
- manual IP appears only as fallback;
- normal UI exposes no raw technical errors;
- at most one primary next action;
- blocked states provide a human explanation and recovery route;
- test output provides machine-readable timing and failed stage.

### P0.2 Health Dashboard integration
Use existing health evidence rather than building a parallel health engine. Present ready, attention, problem or unknown; a concise summary; affected device or station area; and one Next Best Action.

A numeric health percentage is optional and must not be guessed. Add it only with a deterministic tested calculation.

### P0.3 Device Center integration
Create one presentation boundary for supported cameras, vehicles/flight controllers and operator controllers while preserving separate physical identities. Show name, type, observed version, health and last observed activity. Group automatically.

### P0.4 Human Message Layer audit
Audit QML and backend presentation boundaries for raw exception, socket, RTSP, SSH, transport, traceback and internal reason-code leakage. Every normal failure must show practical impact and recommended action. Technical details remain progressively disclosed.

### P0.5 Timeline integration
Convert meaningful startup, discovery, configuration, backup, update and recovery events into human-readable chronological entries. Do not make raw logs the normal experience.

### P0.6 Backup and one-click recovery
Before critical reversible configuration changes, create an identity-bound validated backup and provide a clear restore action. Ambiguous or invalid restore fails closed with a human explanation.

### P0.7 Physical OpenIPC Hardware E2E | RELEASE-BLOCKING PHYSICAL EVIDENCE
Complete real-hardware evidence for verified identity, compatible artifact, guarded update, reboot-pending, bounded rediscovery, hardware continuity, observed post-update firmware and sanitized staged evidence.

This gate blocks hardware-dependent production claims. It does not replace P0 user-journey work and cannot be satisfied by simulation or CI.

## P1: Extensibility and recovery quality
### P1.1 Plugin Host
Define a versioned plugin contract for metadata, capabilities, discovery hooks, health hooks and safe actions. Plugins cannot bypass common presentation, backup, secret or safety boundaries.

### P1.2 Diagnostics 2.0
Complete practical finding -> evidence -> known safe fix -> revalidation. Integrate with Health, Timeline and Next Best Action. Preserve sanitized support bundles and progressive disclosure.

### P1.3 Controller onboarding
Complete automatic local discovery/restore, live input acquisition, durable non-secret profile persistence, health integration and task-oriented calibration/mapping. Keep manual transport in Advanced.

### P1.4 Smart Search
Support natural task language and route to the relevant action or surface rather than exposing internal component names.

### P1.5 Automated UI Review Harness
Add canonical UI states, render/startup smoke, screenshots or equivalent review artifacts and Windows/QML CI validation before final UI consolidation.

## P2: Later product layers
### P2.1 Optional accounts and synchronized device registry
Local operation remains usable offline. Cloud metadata never substitutes for fresh local observation.

### P2.2 Sharing and ownership transfer
Use explicit least-privilege permissions. Never share credentials or bypass local safety gates.

### P2.3 In-app assistant
Consume sanitized structured evidence only. Advisory explanations are allowed; safety authority is not.

### P2.4 Predictive diagnostics and analytics
Introduce only after diagnostic evidence and privacy boundaries are stable. Do not add dashboards without a clear user decision they improve.

### P2.5 Profile system
Synchronize eligible non-secret user preferences only after local identity, restore and conflict behavior are deterministic.

## Release readiness
After the integrated operator journey is stable:
- finalize video-first UX and remove duplicated/dead normal workflows;
- confirm Advanced versus Service Mode boundaries;
- validate Windows packaging, installer layout and startup readiness;
- preserve signed manifest/package integrity and atomic rollback;
- run packaged first-run acceptance;
- complete physical Hardware E2E for hardware-dependent claims;
- publish production release only when software, packaged and physical evidence gates are satisfied.

## Progress reporting
Report separate measures for:
- product-journey acceptance;
- repository-software acceptance;
- packaged application acceptance;
- physical hardware acceptance;
- production release readiness.

Do not combine them into a misleading single success claim. If a percentage is used, state its denominator and completion criteria.

## Next largest safe batch
The next highest-value batch is **P0.1 First-Run Acceptance Harness** using the existing E2/E3/E4 foundations. It must expose exact failed stage and timing, establish the less-than-10-second health target under declared conditions, and protect the normal path from manual configuration and raw technical messages.

## Handoff rule
1. Refresh current `main` and inspect active PR/CI state.
2. Repair an active red baseline before unrelated work.
3. Validate canonical state and safety invariants.
4. Select the highest user-value dependency-valid vertical slice.
5. Update implementation, tests and canonical documentation together.
6. On authorized green merge, refresh `main`, re-audit User Effort and continue.
7. Stop only for physical action, secret, genuine product decision, exhausted bounded automation or unresolved evidence inconsistency.