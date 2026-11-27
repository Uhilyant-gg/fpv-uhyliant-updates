# FPV Uhyliant canonical delivery roadmap

Current `main` plus the canonical documents are authoritative. This roadmap is ordered by user value, dependency and evidence, not by feature count.

## Delivery policy
The product is UX-first, automation-first and zero-config-first. Safety invariants remain authoritative.

Continuous loop:

`audit current main -> largest verified user pain -> smallest high-value vertical slice -> tests -> reviewable PR -> repair red / authorized merge green -> refresh main -> re-audit`

Never treat software CI as physical hardware evidence. Never allow a deferred physical step to justify a physical success claim. Independent software UX work may continue while physical validation awaits hardware or operator action.

## Current audited state
- No aggregate completion percentage is reported; the integrated operator journey and physical acceptance remain incomplete.
- E2 Unified Health, E3 Next Best Action, E4 Zero-Config Startup, E5 Project Doctor, E6 Hardware Simulator and E7 Scenario-Driven CI are complete at the repository-software boundary.
- E0 real OpenIPC Hardware E2E remains physically incomplete.
- E8 controller calibration/mapping/profile core exists, but controller discovery, live acquisition, durable persistence and onboarding remain incomplete.
- The largest product risk is the absence of one evidenced integrated first-run journey that proves the user can launch, understand state, see devices and receive a useful next action without documentation or configuration editing.
- A controlled offscreen full-app run now records all seven first-run stages and is accepted: health evidence appears in 1.67 seconds, with a useful `find-camera` action and no manual configuration or raw UI error. Simulated discovery transitions also appear in Timeline; updater and MAVLink side effects were stubbed. A packaged Windows startup-diagnostics run passed on `8bf09d7`, reaching Qt/QML event-processing completion in 469 ms; this diagnostic does not exercise the visible first-run health, device or next-action journey. Neither run is full packaged-user or physical acceptance. A normal desktop and hardware-backed journey remain unverified.

## Canonical capability status
These headings are retained as the machine-validated capability contract.

### E0 - Physical OpenIPC Hardware E2E | BLOCKED ON PHYSICAL EVIDENCE
Real-hardware acceptance remains incomplete and release-blocking for hardware-dependent claims. Simulation and CI cannot satisfy it.

### E2 - Unified Health and Evidence Contract | COMPLETE
Repository-software acceptance is complete.

### E3 - Next Best Action Engine | COMPLETE
Repository-software acceptance is complete.

### E4 - Zero-Config Startup and Restore | COMPLETE
Repository-software acceptance is complete.

### E5 - Project Doctor and Machine-Readable Project State | COMPLETE
Repository-software acceptance is complete. Project Doctor remains software evidence only.

### E6 - Hardware Simulator and Fault Injection | COMPLETE
Repository-software acceptance is complete. Simulator evidence is never physical evidence.

### E7 - Scenario-Driven CI | COMPLETE
Repository-software acceptance is complete.

## P0: Integrated user journey
### P0.1 First-Run Acceptance Harness | ACTIVE
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

**Repository-software evidence:** startup records launch, restore, automatic discovery start, health, device counts and next action; `main.py --acceptance-report` evaluates the latest run and emits the exact failed stage plus health elapsed time against the 10-second target. A controlled offscreen full-app run passed all seven stages with health evidence in 1.67 seconds. A Windows CI workflow now builds the packaged app and checks that its visible empty-device first-run state and `find-camera` action appear within 10 seconds, using a network-free fixture that explicitly suppresses discovery requests. This verifies the packaged UI path, not live device discovery; physical operation evidence remains uncollected.

### P0.2 Health Dashboard integration
Use existing health evidence rather than building a parallel health engine. Present ready, attention, problem or unknown; a concise summary; affected device or station area; and one Next Best Action.

A numeric health percentage is optional and must not be guessed. Add it only with a deterministic tested calculation.

**Repository-software status:** complete. The operational Home now presents the canonical health state, verified-device counts, human-readable summary and one deterministic Next Best Action. Device and stream changes refresh the model without technical protocol details.

### P0.3 Device Center integration
Create one presentation boundary for supported cameras, vehicles/flight controllers and operator controllers while preserving separate physical identities. Show name, type, observed version, health and last observed activity. Group automatically.

**Implemented foundation (repository software):** the saved-device view now groups records by device category and shows the observed identity health, firmware version and time of the last successful camera observation. A missing version or observation remains explicitly unknown; editing or manually entering an address does not count as activity. Current discovery and saved-device integrations remain camera-focused; controller/vehicle discovery, durable identity integration and their onboarding remain incomplete.

### P0.4 Human Message Layer audit
Audit QML and backend presentation boundaries for raw exception, socket, RTSP, SSH, transport, traceback and internal reason-code leakage. Every normal failure must show practical impact and recommended action. Technical details remain progressively disclosed.

**Additional audit fix (repository software):** backup service outcomes now use Ukrainian, actionable messages and never include raw filesystem exceptions or paths. The current backup panel already uses similarly safe user-facing copy.

**Implemented foundation (repository software):** the existing normal QML boundaries for video, pairing and firmware now use human explanations and recovery hints. Video player failures ignore raw backend strings, stall messages allow only known human text, firmware/update failures hide transport and filesystem details, and validation messages do not echo untrusted manifest values. The reviewed MAVLink diagnostics screen maps link-health labels and displays observed metrics without binding the runtime exception string. Service Mode now shows localized status summaries without telemetry-provider, navigation-source or network-transport identifiers, and unknown status values fail closed to a human message.

### P0.5 Timeline integration
Convert meaningful startup, discovery, configuration, backup, update and recovery events into human-readable chronological entries. Do not make raw logs the normal experience.

**Implemented foundation (repository software):** Timeline presents localized station start, camera selection, video, telemetry, network, navigation, device-discovery lifecycle, device add/update/remove/restore, encrypted backup creation, successfully saved station-OSD settings and meaningful application-update events, while filtering internal diagnostic messages. Rapid OSD slider saves are coalesced into one timeline entry. Only allowlisted event codes and timestamps are stored locally, capped at 200 events or 30 days, with one-click clearing. Other configuration, automatic backup and recovery coverage remains incomplete.

### P0.6 Backup and one-click recovery
Before critical reversible configuration changes, create an identity-bound validated backup and provide a clear restore action. Ambiguous or invalid restore fails closed with a human explanation.

**Implemented foundation (repository software):** Home now exposes the existing encrypted device/stream backup: password-confirmed export, password-verified import, a clear replacement warning and explicit restore confirmation. Passwords are cleared from the UI after use and are not persisted; Timeline records backup creation, and restore emits the existing device-list recovery event. Automatic pre-change snapshots and inclusion of station OSD preferences remain incomplete.

### P0.7 Physical OpenIPC Hardware E2E | RELEASE-BLOCKING PHYSICAL EVIDENCE
Complete real-hardware evidence for verified identity, compatible artifact, guarded update, reboot-pending, bounded rediscovery, hardware continuity, observed post-update firmware and sanitized staged evidence.

This gate blocks hardware-dependent production claims. It does not replace P0 user-journey work and cannot be satisfied by simulation or CI.

### P0.8 Starlink management and live FPV map
Make Starlink operation and location awareness part of the video-first FPV workspace, while keeping observed device capabilities and data freshness explicit.

Requirements:
- provide a dedicated Starlink management surface plus a persistent compact status on the FPV screen;
- show supported terminal/router state and controls only after identifying the model and confirming its available interface;
- keep the update/reboot indicator visible through update, reboot-required, rebooting, reconnection, online and failure states;
- warn that an operation may interrupt connectivity, then revalidate route, video, telemetry and control independently before reporting readiness;
- show separate Starlink, 4G/5G, active route, video, telemetry and control states; do not imply that terminal connectivity proves end-to-end flight readiness;
- integrate video and map side by side or with a clear switch;
- show drone position, direction and track from fresh observed flight-controller GNSS telemetry;
- show Starlink terminal location as a separate marker only when supplied by the verified terminal/API;
- show source and last-update time for both positions; stale or missing data must never look live, and track points must come from observed fresh coordinates;
- support cached/offline map data where the selected provider permits it, and give the operator control over retained location history;
- verify UI states in tests/simulation, then validate supported Starlink hardware behavior physically. Simulation is not physical evidence.

Do not assume a Starlink model/API, modem control capability, or automatic 4G/5G failover. Establish the supported hardware and interface before implementing mutating controls or route switching.

### P0.9 Multi-controller, multi-vehicle and multi-display workspace
Support several detected operator controllers and separate operation sessions for multiple vehicles, while keeping each vehicle's camera, telemetry, map and controller assignment distinct. A controller is assigned to a vehicle session, not a camera.

**Implemented foundation (repository software):** the primary and secondary video streams can each open in a separate movable window, select a detected display, and return to the main workspace without changing their media source; the station OSD follows each stream. When a tracked display is removed, its detached stream returns to the main workspace with playback preserved and a brief explanation. Topology-aware layout restore, physical unplug validation, and multi-vehicle identity isolation remain incomplete.

Requirements:
- automatically discover and add multiple supported controllers in one onboarding flow; identify each controller and bind its profile to stable observed identity;
- make controller-to-vehicle assignments explicit and persistent; prevent silent cross-assignment when changing screen focus or reconnecting devices;
- provide a video-first workspace for at least two separately identified vehicle sessions, each with its own camera streams, map, telemetry and controller status;
- first validate simultaneous monitoring, then enable simultaneous control only after the supported hardware and independent sessions pass simulator, bench and physical acceptance;
- let operators move streams to another monitor by drag-and-drop or an explicit action, detach/re-attach streams without restarting them, and choose a target display;
- offer useful workspace presets and restore layouts only when monitor topology is unambiguous;
- if a monitor disconnects, return its stream to the main workspace and preserve the session;
- test multiple-controller discovery, assignment persistence, isolated session state, window movement, display removal and recovery.

### P0.10 Layered OSD with flight-controller passthrough
Complete the station OSD so it remains glanceable and useful without hiding or replacing the OSD already present in the aircraft's incoming video.

**Implemented foundation (repository software):** users can persistently toggle and configure a compact station overlay, adjust its background opacity and text size, choose one of four screen corners, reset to defaults, and preview its layout from Home or Service mode. The overlay presents available telemetry and video state, marks missing values as unavailable, follows detached streams, and leaves incoming video unchanged. Adaptive per-vehicle profiles, per-field freshness, and real-video readability validation remain incomplete.

Requirements:
- preserve the source video and its existing OSD by default;
- independently control the station-generated OSD, with clear modes for source OSD, station OSD, and both;
- when both are shown, provide a readable non-overlapping default layout and let users configure the station overlay outside active operation;
- state clearly that an OSD burned into video pixels cannot be independently removed by the station;
- bind every overlay to the correct vehicle and stream, including detached video windows and multi-display layouts;
- normalize telemetry values across supported providers, with source, units and per-field freshness; unknown/stale data must not appear current;
- provide a minimal default plus optional navigation/link widgets, a preview, reset-to-default option and per-vehicle profile; do not require manual configuration files;
- keep the central image unobstructed, support readable scaling/contrast, and avoid interaction or layout editing during active operation;
- validate layout readability against real video and across supported display sizes without obscuring important imagery.

### P0.11 Per-vehicle preflight, alerts and offline continuity
Help the operator understand the readiness of each vehicle session and recover from interruptions without mixing evidence or requiring cloud access.

**Implemented foundation (repository software):** an accessible preflight view summarizes observed camera, video, telemetry, GPS freshness, network, navigation and station-OSD state, shows the current next action, and explicitly states that flight control is not integrated. It is an informational checklist, not a flight-readiness authorization; per-vehicle sessions, prioritized alerts and offline recovery remain incomplete.

Requirements:
- provide a concise preflight summary for controller, video, telemetry, network, position freshness and OSD, using observed evidence only;
- show at most one contextually useful next action and explain unknown/blocked states in human language;
- prioritize and deduplicate alerts, keep critical conditions visible, and do not obscure the central video;
- record significant device, video, telemetry and Starlink state transitions in a human-readable session timeline;
- provide sanitized diagnostic export and clear retention controls for session/location history;
- keep local profiles and workspace layouts available offline; use cached maps when supported and clearly disclose missing remote resources;
- test component loss/restoration, stale data and offline restart separately from physical acceptance.

## P1: Extensibility and recovery quality
### P1.1 Plugin Host
Define a versioned plugin contract for metadata, capabilities, discovery hooks, health hooks and safe actions. Plugins cannot bypass common presentation, backup, secret or safety boundaries.

### P1.2 Diagnostics 2.0
Complete practical finding -> evidence -> known safe fix -> revalidation. Integrate with Health, Timeline and Next Best Action. Preserve sanitized support bundles and progressive disclosure.

### P1.3 Smart Search
Support natural task language and route to the relevant action or surface rather than exposing internal component names.

### P1.4 Automated UI Review Harness
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
Report separate measures for product-journey acceptance, repository-software acceptance, packaged application acceptance, physical hardware acceptance and production release readiness.

Do not combine them into a misleading single success claim. If a percentage is used, state its denominator and completion criteria.

## Next largest safe batch
The next highest-value batch is **P0.3 Device Center integration** using the existing discovery and device-health evidence. Present device name, type, observed version, state and last activity in a naturally grouped view, with fixture-backed software tests and no claim of physical discovery until authorized hardware is available.

## Handoff rule
1. Refresh current `main` and inspect active PR/CI state.
2. Repair an active red baseline before unrelated work.
3. Validate canonical state and safety invariants.
4. Select the highest user-value dependency-valid vertical slice.
5. Update implementation, tests and canonical documentation together.
6. On authorized green merge, refresh `main`, re-audit User Effort and continue.
7. Stop only for physical action, secret, genuine product decision, exhausted bounded automation or unresolved evidence inconsistency.
