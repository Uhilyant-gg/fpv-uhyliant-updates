# FPV Uhyliant canonical delivery roadmap

This file is the durable implementation plan for FPV Uhyliant. It is independent of chat history and of any particular AI assistant. Current `main` plus the canonical documents are authoritative.

## Operating model

Development is autonomous by default. User participation should be limited to:
- physical actions with cameras, controllers or other hardware;
- credentials, secrets or keys that must not be supplied to automation;
- product judgement such as reviewing a completed UX and deciding whether it is desirable.

For engineering work use the strict delivery loop:

`current main -> largest safe logically complete batch -> tests -> one commit -> CI -> stop`

Do not start a new implementation batch on red CI. Repair the failing batch first. Do not claim physical success from software CI.

## Planning model

The Jira-style hierarchy below is canonical even when Jira is unavailable. Epic IDs and Story IDs are stable planning identifiers. One implementation commit may close multiple stories when they form one logically complete batch.

Estimates are planning ranges in active engineering days for one autonomous engineering stream. They exclude waiting for CI, hardware availability, external services and product decisions.

### Critical path

`E0 -> E1 -> E2 -> E3 -> E4 -> E9 -> E14 -> E15`

Parallel enabling path:

`E2 -> E5 -> E6 -> E7 -> E15`

Other dependencies:
- E8 depends on E2 and E3 and feeds E14.
- E10 depends on E2 and E4.
- E11 depends on E10 and feeds E14.
- E12 depends on E9 and feeds E14.
- E13 depends on E2 and E3 and supports E14.

## Epic E0 - Physical OpenIPC Hardware E2E
Estimate: 1-2 active engineering days plus physical hardware time.
Dependencies: provenance-validated Hardware E2E artifact.
Critical path: yes.

Stories:
- E0-S1 Execute the validated physical build with a real OpenIPC camera.
- E0-S2 Validate discovery/restore, reachability, verified OpenIPC and observed platform/sensor.
- E0-S3 Validate compatible firmware acquisition, artifact verification and bound preflight evidence.
- E0-S4 Supply session credentials, explicitly accept the SSH host key and perform one deliberate normal update.
- E0-S5 Validate reboot-pending, bounded rediscovery, hardware continuity, observed firmware and terminal evidence.
- E0-S6 If physical validation fails, preserve evidence and repair only the observed blocker before repeating.

Acceptance criteria:
- Fresh verified OpenIPC evidence exists before update.
- Platform and sensor are observed, not inferred.
- Firmware artifact is verified and bound to the approved execution plan.
- Credentials and SSH host-key acceptance are explicit session gates.
- Destructive update requires an explicit operator action.
- Successful dispatch becomes reboot-pending, never immediate success.
- Post-reboot verification requires fresh OpenIPC, matching hardware identity and non-empty observed firmware.
- Preflight and terminal evidence are preserved.
- Outcome is VERIFIED or a concrete evidence-backed blocker.

## Epic E1 - Automated Hardware Validation
Estimate: 5-7 days.
Dependencies: E0.
Critical path: yes.

Stories:
- E1-S1 Implement the pure validation state model and transition contract.
- E1-S2 Orchestrate automatic discovery/restore and deterministic device selection.
- E1-S3 Orchestrate OpenIPC probing and observed hardware identity.
- E1-S4 Orchestrate firmware resolution, download/cache and artifact verification.
- E1-S5 Build immutable device-artifact-plan transaction preparation.
- E1-S6 Add guided credentials and explicit host-key gates.
- E1-S7 Add explicit destructive confirmation as a non-skippable state.
- E1-S8 Automate reboot wait, rediscovery and post-update verification.
- E1-S9 Automate preflight/post-update/failure evidence capture and reason codes.
- E1-S10 Replace the manual Hardware E2E checklist with a compact guided validation UI.

Acceptance criteria:
- One Start validation action performs the complete non-destructive sequence automatically.
- Operator input is requested only for genuine ambiguity, credentials, host-key acceptance and destructive confirmation.
- Existing safety gates remain authoritative and are not reimplemented as weaker checks.
- Transaction mutations invalidate pre-dispatch readiness.
- Post-dispatch verification remains bound to the dispatched transaction.
- VERIFIED is impossible without fresh post-reboot evidence.
- Failure contains failed stage, reason code and sanitized evidence.
- Automated transition and destructive-bypass regression tests are green.

## Epic E2 - Unified Health and Evidence Contract
Estimate: 3-5 days.
Dependencies: E1.
Critical path: yes.

Stories:
- E2-S1 Define common state/health/evidence/next-action schema.
- E2-S2 Define stable reason-code taxonomy.
- E2-S3 Adapt camera and network state.
- E2-S4 Adapt video and firmware state.
- E2-S5 Adapt telemetry and vehicle/controller state.
- E2-S6 Normalize sanitized evidence and correlation data.
- E2-S7 Define safe-action contract for deterministic remediation.

Acceptance criteria:
- Supported subsystems expose state, health, summary, reasonCode, evidence and safeActions through a common contract.
- User-facing health is only ready, attention, problem or unknown.
- Unknown never becomes ready without evidence.
- Missing telemetry is not synthesized.
- Cached/cloud metadata is not fresh hardware evidence.
- Consumers do not need subsystem-specific state-machine knowledge for normal presentation.

## Epic E3 - Next Best Action Engine
Estimate: 2-4 days.
Dependencies: E2.
Critical path: yes.

Stories:
- E3-S1 Define deterministic NBA decision model and priority rules.
- E3-S2 Implement camera/discovery actions.
- E3-S3 Implement video/connect actions.
- E3-S4 Implement firmware and diagnostic actions.
- E3-S5 Implement controller actions.
- E3-S6 Integrate NBA into the FPV workspace.

Acceptance criteria:
- Normal UI exposes at most one primary recommended action for the current context.
- No camera recommends discovery/manual fallback as appropriate.
- Usable camera converges toward video.
- Verified compatible update can recommend Update without bypassing confirmation.
- Deterministic non-destructive remediation can recommend Fix.
- Unresolved problems recommend Diagnose.
- Unknown state never creates unsafe recommendations.

## Epic E4 - Zero-Config Startup and Restore
Estimate: 4-7 days.
Dependencies: E2, E3.
Critical path: yes.

Stories:
- E4-S1 Restore previously known non-secret device metadata.
- E4-S2 Start automatic local discovery.
- E4-S3 Select a device automatically only when evidence is unambiguous.
- E4-S4 Select a usable stream automatically when safe.
- E4-S5 Enter the FPV workspace directly when a usable camera is known.
- E4-S6 Keep manual IP as fallback.
- E4-S7 Surface startup failure through health and NBA.

Acceptance criteria:
- Happy path is launch -> restore/discover -> verified usable camera -> video.
- Returning operator is not forced through a dashboard.
- Manual IP is not a peer default workflow.
- Ambiguity is never guessed.
- Failure produces a practical next action.
- Video retains the largest useful area.

## Epic E5 - Project Doctor and Machine-Readable Project State
Estimate: 3-5 days.
Dependencies: E2.
Critical path: enabling.

Stories:
- E5-S1 Add machine-readable canonical project-state schema.
- E5-S2 Add capability matrix with lifecycle statuses.
- E5-S3 Add canonical-document consistency checks.
- E5-S4 Implement project doctor orchestration.
- E5-S5 Emit machine-readable READY/BLOCKED area-stage-reason output.
- E5-S6 Integrate doctor checks into CI without replacing domain tests.

Acceptance criteria:
- A single doctor command returns READY or a precise BLOCKED result.
- Current phase, capability status and next milestone are machine-readable.
- Canonical drift is detectable.
- A new development session can establish current project state from current main without historical chat context.
- Human-readable canonical docs remain authoritative for product intent.

## Epic E6 - Hardware Simulator and Fault Injection
Estimate: 6-10 days.
Dependencies: E1, E2.
Critical path: enabling.

Stories:
- E6-S1 Implement simulated OpenIPC discovery/device endpoint.
- E6-S2 Simulate identity, platform, sensor and firmware observations.
- E6-S3 Simulate authentication and update dispatch outcomes.
- E6-S4 Simulate reboot and DHCP-address changes.
- E6-S5 Simulate multiple OpenIPC devices and identity competition.
- E6-S6 Add fault-injection framework.
- E6-S7 Add Hardware E2E scenario fixtures.

Acceptance criteria:
- CI can exercise happy-path update without physical hardware.
- CI can inject authentication failure, disappearance, DHCP change, wrong camera, identity mismatch, missing firmware, malformed evidence, network loss and artifact corruption.
- Simulator cannot be reported as physical validation.
- Physical-only acceptance remains explicit.

## Epic E7 - Scenario-Driven CI
Estimate: 4-7 days.
Dependencies: E5, E6.
Critical path: enabling.

Stories:
- E7-S1 Add startup scenarios.
- E7-S2 Add discovery-to-video scenarios.
- E7-S3 Add firmware lifecycle scenarios.
- E7-S4 Add failure/recovery scenarios.
- E7-S5 Add controller scenarios after E8 primitives exist.
- E7-S6 Emit machine-readable CI failure summaries.
- E7-S7 Remove only redundant brittle source-policy assertions once scenario coverage replaces them.

Acceptance criteria:
- Critical product flows have behavioral scenario coverage.
- Harmless formatting/refactor does not produce false red.
- Safety/behavior regressions produce red.
- Failure output identifies subsystem, stage and reason.
- Security/safety source-policy assertions remain where they protect real invariants.

## Epic E8 - FPV/RC Controller Onboarding
Estimate: 6-10 days.
Dependencies: E2, E3.
Feeds: E14.

Stories:
- E8-S1 Define controller discovery abstraction.
- E8-S2 Implement automatic local detection and restore.
- E8-S3 Observe real input/channel availability.
- E8-S4 Implement calibration.
- E8-S5 Implement stick/switch mapping and validation.
- E8-S6 Persist safe non-secret controller profiles.
- E8-S7 Map controller status to unified health.
- E8-S8 Keep manual transport/port setup in Advanced.
- E8-S9 Integrate controller state contextually into FPV workspace.

Acceptance criteria:
- Automatic detection/restore is preferred where trustworthy.
- Live inputs are observed, never synthesized.
- Calibration has explicit completeness state.
- Mapping can be physically verified.
- Disconnect/reconnect updates health.
- Manual transport configuration is fallback/Advanced.
- Camera, vehicle/flight controller and operator RC controller identities remain distinct.

## Epic E9 - Diagnostics 2.0
Estimate: 4-7 days.
Dependencies: E2, E3. Prefer scenario infrastructure from E7 when available.
Critical path: yes.

Stories:
- E9-S1 Define common diagnostic finding schema.
- E9-S2 Complete reason-code catalogue.
- E9-S3 Automate evidence collection.
- E9-S4 Implement safe remediation registry.
- E9-S5 Implement remediation -> revalidation loop.
- E9-S6 Produce one sanitized support bundle.
- E9-S7 Add progressive technical disclosure.
- E9-S8 Integrate Diagnose/Fix choices with NBA.

Acceptance criteria:
- UI shows the practical problem before implementation detail.
- Diagnose gathers relevant evidence automatically.
- Fix is available only for deterministic non-destructive remediation.
- A Fix is followed by automatic revalidation.
- Technical evidence remains available on demand.
- Export is sanitized.
- Unknown stays unknown.

## Epic E10 - Accounts and Synchronized Device Registry
Estimate: 8-15 days.
Dependencies: E2, E4.

Stories:
- E10-S1 Define account identity/session boundary.
- E10-S2 Define stable cloud DeviceIdentity distinct from mutable network coordinates.
- E10-S3 Define cloud device record schema.
- E10-S4 Implement local/cloud reconciliation.
- E10-S5 Implement cross-workstation device-registry synchronization.
- E10-S6 Implement offline cache and recovery.
- E10-S7 Synchronize eligible non-secret preferences.
- E10-S8 Add account UX without displacing FPV workspace.

Acceptance criteria:
- Account is optional for local FPV operation.
- Added device inventory can restore after sign-in on another workstation.
- IP address is not stable device identity.
- Cloud firmware/health does not masquerade as fresh observation.
- Offline local operation remains functional.
- Session credentials, host-key acceptance and destructive authority are not normally synchronized.

## Epic E11 - Device Sharing and Ownership Transfer
Estimate: 5-8 days.
Dependencies: E10.
Feeds: E14.

Stories:
- E11-S1 Define least-privilege permission model.
- E11-S2 Implement sharing invitation/access.
- E11-S3 Implement access revocation.
- E11-S4 Implement deliberate ownership-transfer transaction.
- E11-S5 Implement completed-transfer cleanup/revocation.
- E11-S6 Add shared-device UX.
- E11-S7 Add sanitized ownership/access audit events.

Acceptance criteria:
- Sharing does not change owner.
- Sharing is revocable.
- Transfer is deliberate and changes owner only on completion.
- Permissions are explicit and least-privilege.
- Shared credentials are not the sharing model.
- Remote permission never bypasses local destructive safety gates.

## Epic E12 - AI Diagnostic Assistant
Estimate: 5-10 days.
Dependencies: E9.
Feeds: E14.

Stories:
- E12-S1 Define AI-safe diagnostic evidence schema.
- E12-S2 Enforce sanitization boundary.
- E12-S3 Generate practical diagnostic explanations from evidence.
- E12-S4 Suggest the next diagnostic action.
- E12-S5 Suggest known-safe remediation where already authorized by deterministic policy.
- E12-S6 Preserve unknown/missing evidence explicitly.
- E12-S7 Integrate assistant contextually into diagnostics/FPV workspace.
- E12-S8 Add safety/adversarial tests.

Acceptance criteria:
- AI receives sanitized structured evidence only.
- AI can explain evidence and suggest diagnostic paths.
- AI receives no secrets through the diagnostic contract.
- AI never establishes authoritative identity, compatibility, ownership or firmware success.
- AI never approves or executes destructive actions.
- Missing evidence remains unknown rather than guessed.

## Epic E13 - Automated UI Review Harness
Estimate: 4-7 days.
Dependencies: E2, E3.
Feeds: E14.

Stories:
- E13-S1 Define deterministic canonical UI-state fixtures.
- E13-S2 Implement startup/render harness.
- E13-S3 Cover disconnected/camera-ready/video states.
- E13-S4 Cover firmware/diagnostic states.
- E13-S5 Cover controller/account/AI states as those capabilities arrive.
- E13-S6 Produce review artifacts/screenshots.
- E13-S7 Integrate smoke validation with CI.

Acceptance criteria:
- Canonical UI states are reproducible without repeated manual setup where physical evidence is not required.
- QML startup/render failures are detected automatically.
- Missing/dead controls are detected before routine product review where practical.
- User participation is primarily visual/product approval.

## Epic E14 - Video-First UX Finalization
Estimate: 6-10 days.
Dependencies: E3, E4, E8, E9. Incorporate completed E11/E12/E13 capabilities when available.
Critical path: yes.

Stories:
- E14-S1 Finalize FPV workspace information architecture.
- E14-S2 Remove duplicated/dead normal workflows.
- E14-S3 Integrate unified health and NBA.
- E14-S4 Integrate controller context.
- E14-S5 Integrate diagnostics context.
- E14-S6 Integrate account/sharing entry points contextually.
- E14-S7 Integrate AI entry point contextually.
- E14-S8 Finalize Advanced versus Service Mode separation.
- E14-S9 Complete responsive/window-state polish.

Acceptance criteria:
- Video occupies the largest practical area.
- Normal workflow is not duplicated across subsystem screens.
- Primary health and next action are discoverable without unnecessary navigation.
- Secondary normal controls are progressively disclosed.
- Recovery/fullflash/Hardware E2E remain Service/Validation workflows.
- Account, controller and AI features do not create competing product home screens.
- Final user involvement can primarily be product review: like/dislike and product-direction decisions.

## Epic E15 - Release, Installer and OTA Production Readiness
Estimate: 5-10 days.
Dependencies: E14. E7 strongly preferred before production release.
Critical path: yes.

Stories:
- E15-S1 Validate production packages.
- E15-S2 Validate Windows installer layout and launch path.
- E15-S3 Validate signed update-manifest path and package integrity.
- E15-S4 Validate OTA/update workflow.
- E15-S5 Validate startup acknowledgement.
- E15-S6 Validate atomic current/rollback behavior.
- E15-S7 Add packaged release smoke scenarios.
- E15-S8 Record release provenance/evidence.
- E15-S9 Define production release gate.

Acceptance criteria:
- Release package passes repeatable validation.
- Installer contains a complete runnable launcher layout.
- Manifest and package integrity remain mandatory.
- Broken candidate cannot silently replace known-good installation.
- Rollback path is tested.
- Packaged startup smoke is green.
- Production artifacts are attributable to exact source.
- Publication happens only after the release gate.

## Dependency-oriented Gantt

Planning horizon below uses relative engineering weeks, not calendar commitments. Work can be reordered only when dependencies and canonical product invariants remain satisfied.

| Epic | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 | W9 | W10 |
|---|---|---|---|---|---|---|---|---|---|---|
| E0 Physical E2E | X | | | | | | | | | |
| E1 Automated Validation | X | X | | | | | | | | |
| E2 Health/Evidence | | X | X | | | | | | | |
| E3 Next Best Action | | | X | | | | | | | |
| E4 Zero-config | | | X | X | | | | | | |
| E5 Project Doctor | | | X | X | | | | | | |
| E6 Simulator/Faults | | | | X | X | X | | | | |
| E7 Scenario CI | | | | | | X | X | | | |
| E8 RC Controllers | | | | X | X | X | | | | |
| E9 Diagnostics 2.0 | | | | X | X | | | | | |
| E10 Accounts | | | | | X | X | X | X | | |
| E11 Sharing/Transfer | | | | | | | | X | X | |
| E12 AI Assistant | | | | | X | X | | | | |
| E13 UI Harness | | | | X | X | | | | | |
| E14 Video-first UX | | | | | | X | X | X | | |
| E15 Release/OTA | | | | | | | | X | X | X |

The critical path is E0 -> E1 -> E2 -> E3 -> E4 -> E9 -> E14 -> E15. Enabling automation E5/E6/E7 should be pulled forward whenever it does not block the critical path because it reduces later manual QA and developer intervention.

## Handoff rule for every chat or AI

At the beginning of any development session:
1. Read current `main`.
2. Read `PRODUCT_UX.md`, `PROJECT_STATE.md`, `DEVELOPMENT_GUIDE.md`, `HARDWARE_E2E.md` and this `DELIVERY_ROADMAP.md`.
3. Determine the first incomplete Epic/Story whose dependencies are satisfied.
4. Prefer the largest safe, logically complete implementation batch within that ready scope.
5. Do not restore code from chat memory over current `main`.
6. Stop only for physical hardware, secrets/credentials/keys, or a genuine product decision.
7. After one implementation commit, stop for CI. On red CI repair that batch before any new functionality.

The target participation model is deliberate: engineering automation handles repository inspection, implementation, tests, simulation, packaging and failure diagnosis; the user handles physical interactions, secrets and final product judgement.
