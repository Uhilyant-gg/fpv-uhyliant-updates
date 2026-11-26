# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Current priority
The guarded OpenIPC update foundation is ready for integrated physical validation. Complete Hardware E2E first, using observed evidence rather than treating software CI as proof of physical success.

After the Hardware E2E lifecycle is proven, product work follows the task-centered zero-config roadmap in `PRODUCT_UX.md`. The target normal experience is:

`launch -> automatic discover/restore -> verified usable camera -> video -> operate`

The product is organized around tasks and a contextually useful next action rather than around subsystem screens. FPV/video becomes the operational home when a usable camera is known.

## Product UX direction
The approved product direction is:

- zero-config first;
- FPV workspace as the operational center;
- one common user-facing health vocabulary: ready / attention / problem / unknown;
- a Next Best Action model instead of exposing subsystem navigation as the primary workflow;
- an operational Home health surface that reuses canonical health evidence and one deterministic next action;
- manual IP as automatic-discovery fallback;
- simplified normal firmware experience;
- practical problem -> diagnose -> known safe fix;
- explicit separation between normal, Advanced and Service Mode;
- Hardware E2E moved to Service/Validation rather than normal operator UI;
- an automation budget: if trustworthy observed evidence can determine something safely and unambiguously, the application should not ask the operator;
- post-Hardware-E2E account/device portability with optional cloud registry, sharing and ownership transfer while preserving offline local operation;
- zero-config-oriented FPV/RC controller onboarding, restore, calibration and mapping;
- later advisory AI assistance over sanitized structured diagnostics, never as authority for destructive actions.

Safety invariants remain authoritative over convenience. Automation never guesses identity, telemetry, compatibility, firmware success or destructive approval.

## Discovery and device identity
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability or ONVIF is not OpenIPC evidence.

Protected endpoints may surface an authentication-required candidate, but authentication alone never upgrades it to verified OpenIPC. Platform, SoC, sensor, variant and firmware remain unknown unless observed. The evidence ladder remains:

`reachable service -> camera candidate -> verified OpenIPC -> separately evidenced R2D2 compatibility -> observed hardware identity -> observed streams`.

Manual IP is a fallback when automatic discovery/restore does not yield a usable device, while an explicitly entered host may still be checked directly within the existing safety boundary.

## Accounts, synchronized device registry and access
Accounts are not required for basic local FPV operation. Loss of Internet/account service must not disable an otherwise locally usable station.

A signed-in user's added-device registry and eligible non-secret preferences may synchronize across workstations. Cloud records are ownership/metadata hints, not current hardware observations. After restore on another workstation, local discovery and observation remain responsible for current address, reachability, identity, firmware, streams, telemetry and health.

Stable device identity is separate from mutable IP/network coordinates. Account-level device access includes explicit sharing and explicit ownership transfer. Sharing is revocable without changing the owner; transfer is a deliberate ownership handoff. Permissions should distinguish viewing/status, normal operation, management and ownership administration rather than relying on shared device credentials.

Remote/account permission never bypasses local safety validation. Session credentials, passwords, accepted SSH host-key state, destructive approvals and comparable ephemeral authority are not normal synchronized device metadata.

## FPV / RC controllers
Cameras, vehicles/flight controllers and operator RC controllers are separate physical entities composed by the FPV workspace.

The normal controller experience should prefer automatic local detection and restore. Manual transport/port selection belongs in Advanced when automatic detection is insufficient. Controller onboarding covers observed connection/input availability, calibration, stick/switch mapping and restoration of the last valid non-secret configuration.

Controller status maps into ready / attention / problem / unknown. Missing or invalid controller evidence remains unknown/blocked rather than simulated. User-owned controller profiles and non-secret preferences may later synchronize with the account, but live input and physical presence remain locally observed.

## Automatic firmware lifecycle
The normal user path uses the selected/active verified OpenIPC camera and derives a supported firmware profile only from observed platform + sensor. A profile is never guessed from a UI choice. If no unique supported profile exists, automatic update remains blocked.

The official OpenIPC catalog is consumed through a fail-closed acquisition boundary. Only complete entries with observed platform + sensor, explicit variant/channel/build, an allowed HTTPS OpenIPC download URL, SHA-256 and bounded positive size become candidates. Variant/build ambiguity requires an explicit Advanced choice.

Downloaded or cached artifacts must pass exact size and SHA-256 verification before entering Firmware Center. The catalog/artifact/execution path remains bound to the selected device identity and becomes stale on relevant change.

For a normal operator, the target firmware UI is only the observed device/current firmware, a verified available update, practical status and one deliberate Update action. Catalog mechanics and verification stay internal unless intervention is required.

Manual firmware, recovery and fullflash belong in Service Mode. Recovery/fullflash is never a universal OpenIPC update method.

## Destructive update safety
Normal OpenIPC update remains fixed `sysupgrade -k -r` for currently verified compatible OpenIPC only. Credentials are session-only. Passwords must not enter logs, persistence, diagnostics, status, execution plans, shell interpolation or process argv.

Authentication and accepted SSH host-key state precede destructive execution. Immediately before execution, approved device, current host, verified OpenIPC state, observed platform/sensor, approval, execution plan and firmware artifact integrity must still match. Any stale or changed input fails closed.

The destructive operation remains an explicit user action. Successful dispatch means only `reboot-pending`, never successful update.

## Reboot and post-update verification
Post-reboot verification uses the host bound at destructive dispatch and bounded route-aware rediscovery. A changed DHCP address may be accepted only from fresh OpenIPC evidence with matching pre-update platform and sensor. Unrelated OpenIPC devices are skipped.

Success requires fresh verified OpenIPC evidence, hardware continuity and a non-empty actually observed post-update firmware version. For catalog-backed firmware, the selected build is carried through executor handoff as the expected firmware target. Unknown authoritative firmware remains unknown and cannot make a missing observed version pass.

## Diagnostics, observability and AI assistance
Diagnostics is part of the hardware-validation path and later becomes the common problem -> diagnose -> safe-fix product path. User-facing diagnostics first describe the practical fault; technical evidence remains available on demand.

Firmware lifecycle events use bounded structured evidence and a shared correlation id. Diagnostic exports remain sanitized and support distinct preflight, post-update and failure captures so physical failures can be reproduced without overwriting earlier evidence.

Later AI assistance consumes the same sanitized structured evidence. It may explain faults and propose diagnostic or known-safe remediation paths, but it is advisory and never becomes authority for device identity, telemetry, compatibility, credentials, ownership, firmware success, destructive approval or execution. Unknown remains unknown.

## Application updater
The packaged Windows updater remains a parallel release-readiness track. Signed manifest validation and package SHA-256 remain mandatory. Installation is offered only for a complete installed launcher layout. Helper staging, payload self-test, atomic current/rollback switching and startup acknowledgement remain fail-closed.

A build-only Windows pipeline may produce validated Hardware E2E artifacts without publishing release metadata. Application-updater polish must not block OpenIPC hardware E2E unless a packaging defect prevents producing or running the physical-test build.

## Hardware E2E success contract
Software-only CI does not prove physical update success. A Hardware E2E pass requires observed evidence for the same logical camera across the lifecycle:

- verified OpenIPC before update;
- observed platform + sensor before update;
- compatible verified firmware artifact;
- ready preflight bound to the selected camera and artifact/execution plan;
- session credentials and explicit SSH host-key acceptance;
- authenticated guarded destructive execution;
- reboot-pending after dispatch;
- bounded rediscovery after reboot;
- fresh verified OpenIPC identity with matching hardware continuity;
- non-empty observed post-update firmware;
- sanitized staged evidence for preflight and terminal outcome.

If any item is missing, report the stage and evidence instead of claiming update success.

## Execution order
1. Finish real OpenIPC Hardware E2E using a validated build-only Windows artifact.
2. Fix failures found from staged/correlated physical evidence and repeat until the guarded lifecycle completes or a genuine external/hardware blocker is identified.
3. Introduce the unified device/health presentation boundary across cameras, vehicles/controllers and relevant station state.
4. Introduce Next Best Action as the primary normal-workflow navigation model.
5. Make startup zero-config: automatic restore/discovery -> usable camera -> video, with manual IP as fallback.
6. Add FPV/RC controller onboarding: automatic detection/restore first, then calibration, mapping and controller health; keep manual transport configuration in Advanced.
7. Simplify normal Firmware UX while moving manual/recovery/fullflash and Hardware E2E into Service/Validation.
8. Rework diagnostics into practical problem -> diagnose -> known safe fix, with technical details progressively disclosed.
9. Add optional user accounts and synchronized device registry without making cloud availability a requirement for local operation.
10. Add explicit device sharing and ownership transfer with least-privilege permissions; cloud access never bypasses local destructive safety gates.
11. Add advisory AI assistance over sanitized structured diagnostics/evidence after the diagnostic boundary is stable.
12. Complete the larger video-first UI cleanup and remove duplicated/dead normal-workflow controls, integrating account, controller and AI entry points contextually rather than as competing home screens.
13. Finish release/readiness, installer and OTA polish after the integrated operator journey is stable.

Each implementation item is delivered as one logically complete substantial batch. Do not accumulate additional product changes on a failing CI baseline; fix the current batch to green first.

## Stable product invariants
FPV remains video-first. Cameras, vehicles/flight controllers and operator RC controllers remain distinct physical identities composed in the FPV workspace. Camera presets, video profiles and firmware are separate entities. Firmware update must not apply a video profile. Unknown telemetry/state remains unknown. Cloud metadata is not fresh hardware evidence. AI output is advisory, not authority. Recovery/fullflash is separate from normal update. Destructive firmware transport stays disabled at startup and requires the normal explicit safety/approval path.
