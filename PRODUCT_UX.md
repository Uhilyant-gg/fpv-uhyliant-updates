# FPV Uhyliant product and UX principles

## Product goal
FPV Uhyliant should feel like an appliance, not a collection of technical screens: launch -> automatically discover/connect -> show video -> operate. The operator should spend almost all normal operating time in the video workspace.

## Primary rule
Minimize operator effort while maximizing useful automation. Complexity stays hidden until it is needed. Organize the product around user tasks and next actions, not around internal subsystems or transports.

## Default journey
The normal path is:

`launch -> automatic discovery/restore -> verified usable device -> video -> operate`

If no usable camera is found, keep the operator in the same task flow and offer the next safe action. Manual IP is a fallback after automatic discovery, not a peer default workflow.

When something fails, prefer:

`practical problem -> diagnose -> known safe fix`

Technical evidence remains available on demand.

## Video workspace is home during operation
The FPV/video workspace is the product center once a usable working camera is known. Do not force a returning operator through a dashboard before video. First-run, disconnected and recovery states may overlay a minimal onboarding/task surface on the video workspace.

The video area gets the largest useful space. Persistent UI contains only information required for operation, safety, current health and the next useful action. Secondary controls belong in contextual popups, drawers or detail views.

## Zero-config first
Automatic discovery, identification, capability detection, stream selection, safe defaults, compatible firmware selection, artifact verification, rediscovery and post-update verification are preferred wherever they can be determined from trustworthy evidence.

Manual IP addresses, ports, protocol details and other technical controls remain fallback or Advanced controls unless required for the current task.

## Automation budget
Every new user-facing decision must answer: can the application determine this safely and unambiguously from observed evidence?

If yes, automate it and do not ask the operator. If no, ask only for the missing decision or input. Typical operator-owned inputs are session credentials, genuinely ambiguous choices, destructive confirmation and recovery decisions.

Automation must never invent unknown identity, telemetry, compatibility or success.

## Device-centered model
Present a camera or controller as one device rather than exposing transport implementation details as separate concepts. Device details may expose Video, Status, Settings, Firmware and Diagnostics when relevant.

Cameras, vehicles/flight controllers and operator RC controllers remain distinct physical entities. The FPV workspace composes them into one operational context instead of conflating their identity, ownership, health or configuration.

## Accounts, device registry and portability
An account layer is a post-Hardware-E2E product capability, not a prerequisite for local operation. Local FPV operation must remain usable when the account service or Internet is unavailable.

An authenticated user may have a portable registry of added devices and user-owned configuration so that signing in on another workstation can restore the user's device inventory and eligible preferences. Cloud records are metadata and ownership records, not live hardware evidence: cached identity, address, firmware, telemetry or health must never be treated as freshly observed merely because it was synchronized.

Stable device identity must be separated from mutable network coordinates such as IP addresses. Local discovery/restore remains responsible for proving current reachability and current hardware state.

Device access supports two explicit concepts:

- sharing grants revocable access while preserving the existing owner;
- transfer moves ownership through a deliberate handoff and revokes the previous ownership relationship when completed.

Permissions must be explicit and least-privilege. A useful product model distinguishes viewing/status access, normal operation, device management and ownership administration. Cloud permission never bypasses local destructive-action validation, firmware compatibility, observed identity, session authentication or explicit approval.

Session credentials, passwords, accepted SSH host-key state and other ephemeral destructive-operation authority are not normal cloud-synchronized device metadata.

## FPV / RC controller onboarding
Operator controllers belong in the same zero-config product journey without becoming another permanent subsystem screen. A normal controller path should prefer automatic local detection and restore, then expose manual transport/port choices only as an Advanced fallback.

Controller onboarding should cover observed connection state, input/channel availability, calibration, switch/stick mapping and restoration of the last valid configuration. Unknown controller capabilities or inputs remain unknown rather than synthesized.

Controller health uses the same ready / attention / problem / unknown vocabulary. Disconnection, unavailable input, invalid mapping or missing calibration should produce a practical next action or diagnostic path instead of raw transport errors.

Controller profiles and non-secret preferences may later follow the signed-in user across workstations, while current physical presence, live inputs and safety-relevant state must always come from local observation.

## Unified health vocabulary
User-facing health uses only four concepts:

- ready: normal operation can continue;
- attention: operator input or a non-critical prerequisite is needed;
- problem: normal operation is blocked or degraded and action is required;
- unknown: evidence is insufficient.

Subsystem state machines may remain more detailed internally. Technical states such as reconnecting, stalled, reboot-pending or stale are translated into the common health model for normal UI and remain visible in technical details.

Unknown remains unknown and must never be converted into guessed telemetry, device identity or health.

## Next Best Action
The default UI should emphasize one contextually useful next action rather than a permanent toolbar of subsystem destinations.

Examples:
- no camera -> Find camera;
- discovered usable camera -> Connect;
- connected camera with usable stream -> Show video;
- missing controller -> Connect controller;
- controller requiring calibration -> Calibrate controller;
- verified compatible update -> Update;
- recoverable non-destructive fault -> Fix;
- unresolved fault -> Diagnose.

A next action must respect all existing safety boundaries. Destructive actions remain deliberate and explicit.

## Progressive disclosure
Normal mode stays simple and task-oriented.

Advanced contains additional controls for normal operation: manual IP/ports, stream choices, controller transport/mapping details, protocol details, telemetry details and diagnostic evidence.

Service Mode contains specialist, recovery or developer/maintenance workflows: recovery/fullflash, manual firmware operations, low-level configuration, developer diagnostics and Hardware E2E validation.

Hardware E2E is a Service/Validation workflow, not a normal operator feature. The normal firmware lifecycle performs the same required verification internally without exposing a separate Hardware E2E step.

## Safe automation and AI assistance
A one-click fix is appropriate only for deterministic, non-destructive remediation. Destructive operations continue through existing validation and approval boundaries.

AI assistance is a later product layer over sanitized structured evidence. It may explain practical faults, summarize evidence and propose diagnostic or known-safe remediation paths. AI is advisory: it never becomes authority for device identity, telemetry, compatibility, credentials, ownership, firmware success, destructive approval or destructive execution.

AI assistance must consume the same sanitized evidence boundary used by diagnostics and preserve unknown values rather than filling gaps with guesses.

## Firmware experience
For a normal operator, firmware should reduce to device identity, observed current firmware, verified available update, a short practical status and one deliberate Update action.

Catalog resolution, compatible profile derivation, download, SHA-256/size integrity, immutable device binding, execution plan, reboot rediscovery and post-update verification remain internal unless intervention is required.

Credentials are requested only for the session when they are actually required. Ambiguous catalog selection belongs in Advanced. Manual firmware, recovery and fullflash belong in Service Mode and must never be presented as the recommended normal update path.

## Diagnostics experience
Show the practical fault first. Offer Diagnose when more evidence is required, and Fix only when a deterministic non-destructive remediation is known. Technical errors, logs, evidence and correlation details stay behind an explicit details path.

Diagnostic exports remain sanitized, preserve unknown values and support staged evidence capture for hardware validation. The same structured evidence is the boundary for later AI-assisted diagnosis.

## UI quality rules
Do not expose dead controls. If an action is unavailable, explain the practical reason and, where known, the missing prerequisite.

Do not require navigation to learn that an obvious next action is available. Do not duplicate the same normal workflow across Home, Devices, Firmware and Diagnostics.

Critical operational information must remain glanceable without consuming the video workspace with low-priority data.

Account, sharing, controller and AI capabilities should surface contextually in the existing task flow rather than creating competing home screens.

## Product decision tests
For every visible control or requested decision ask:

1. Does it make the operator faster, safer or the situation clearer?
2. Can the application determine it safely without asking?
3. Is it needed during normal operation, or does it belong in Advanced/Service Mode?
4. Is the operator being shown the practical problem before implementation detail?
5. Does the change preserve the largest useful video area?
6. Is synchronized/cloud state being kept distinct from fresh local hardware evidence?
7. Does any AI or remote permission preserve the local safety authority boundaries?

If a visible element fails these tests, automate it, move it behind progressive disclosure or remove it from the normal workflow.
