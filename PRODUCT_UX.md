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
- verified compatible update -> Update;
- recoverable non-destructive fault -> Fix;
- unresolved fault -> Diagnose.

A next action must respect all existing safety boundaries. Destructive actions remain deliberate and explicit.

## Progressive disclosure
Normal mode stays simple and task-oriented.

Advanced contains additional controls for normal operation: manual IP/ports, stream choices, protocol details, telemetry details and diagnostic evidence.

Service Mode contains specialist, recovery or developer/maintenance workflows: recovery/fullflash, manual firmware operations, low-level configuration, developer diagnostics and Hardware E2E validation.

Hardware E2E is a Service/Validation workflow, not a normal operator feature. The normal firmware lifecycle performs the same required verification internally without exposing a separate Hardware E2E step.

## Safe automation
A one-click fix is appropriate only for deterministic, non-destructive remediation. Destructive operations continue through existing validation and approval boundaries. AI diagnosis, if introduced, is advisory and never becomes authority for destructive actions.

## Firmware experience
For a normal operator, firmware should reduce to device identity, observed current firmware, verified available update, a short practical status and one deliberate Update action.

Catalog resolution, compatible profile derivation, download, SHA-256/size integrity, immutable device binding, execution plan, reboot rediscovery and post-update verification remain internal unless intervention is required.

Credentials are requested only for the session when they are actually required. Ambiguous catalog selection belongs in Advanced. Manual firmware, recovery and fullflash belong in Service Mode and must never be presented as the recommended normal update path.

## Diagnostics experience
Show the practical fault first. Offer Diagnose when more evidence is required, and Fix only when a deterministic non-destructive remediation is known. Technical errors, logs, evidence and correlation details stay behind an explicit details path.

Diagnostic exports remain sanitized, preserve unknown values and support staged evidence capture for hardware validation. The same structured evidence may later support AI-assisted diagnosis.

## UI quality rules
Do not expose dead controls. If an action is unavailable, explain the practical reason and, where known, the missing prerequisite.

Do not require navigation to learn that an obvious next action is available. Do not duplicate the same normal workflow across Home, Devices, Firmware and Diagnostics.

Critical operational information must remain glanceable without consuming the video workspace with low-priority data.

## Product decision tests
For every visible control or requested decision ask:

1. Does it make the operator faster, safer or the situation clearer?
2. Can the application determine it safely without asking?
3. Is it needed during normal operation, or does it belong in Advanced/Service Mode?
4. Is the operator being shown the practical problem before implementation detail?
5. Does the change preserve the largest useful video area?

If a visible element fails these tests, automate it, move it behind progressive disclosure or remove it from the normal workflow.
