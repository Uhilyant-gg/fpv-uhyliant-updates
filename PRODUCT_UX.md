# FPV Uhyliant Product Constitution

This document is the primary product decision authority. When feature growth, technical convenience, schedule pressure or subsystem ownership conflicts with the normal user journey, this constitution wins unless a safety invariant requires otherwise.

## Product mission
FPV Uhyliant must feel like an appliance, not a collection of technical screens.

The normal user should be able to:
1. install the application;
2. launch it;
3. see all available supported devices;
4. understand system state in less than 10 seconds;
5. avoid manual configuration editing;
6. avoid external documentation for normal tasks;
7. receive explanations and recommended actions in plain human language.

Target journey:

`install -> launch -> automatic discovery/restore -> system state -> verified usable device -> video -> operate`

If a normal first-run or recovery journey requires README instructions, a terminal, configuration editing, knowledge of IP addresses or interpretation of technical errors, treat that as a product defect.

## Decision hierarchy
Evaluate every proposed change in this order:
1. Does it remove a verified user pain?
2. Does it reduce clicks, elapsed time, manual input or documentation dependency?
3. Can the application perform it automatically and safely?
4. Can technical parameters remain hidden from the normal workflow?
5. Does the result explain itself in human language?
6. Does it improve stability, recovery or confidence?
7. Only then consider feature breadth.

A change that adds capability but does not improve the user journey is lower priority.

## Principle 1: UX First
Every feature is evaluated by user impact. Prefer completing one coherent journey over adding another subsystem screen.

The UI is task-centered and state-centered. Internal modules, transports and protocols must not define primary navigation.

## Principle 2: Automation First
Any action that can be determined and completed safely from trustworthy observed evidence must be automated.

Ask the user only for decisions the application cannot safely make, including session credentials, genuinely ambiguous choices, destructive confirmation and recovery decisions.

## Principle 3: Zero Config First
Any parameter that can be discovered or derived safely must not be requested in the normal flow.

Manual IP, ports, protocols, stream details and transport selection are fallback or Advanced controls. They are never peer defaults beside automatic discovery.

Automation must never invent identity, telemetry, compatibility, ownership, firmware success or physical acceptance. Unknown remains unknown.

## Principle 4: Human Language Only
Normal UI must not expose raw transport, protocol, socket, exception or traceback text.

Every user-facing problem uses this shape:
- what happened;
- what it means for the current task;
- likely causes when evidence supports them;
- one recommended next action;
- optional technical details behind progressive disclosure.

Example:

`Не вдалося підключитися.`

`Можливі причини: пристрій недоступний або мережеве з'єднання ще не готове.`

`Рекомендована дія: перевірити підключення.`

Stable internal reason codes remain available for tests, support and diagnostics, but are not the primary message.

## Principle 5: Documentation Last
The ideal normal user never opens README. Documentation supports developers, service work and exceptional recovery. It must not compensate for an unclear normal workflow.

## User Effort Score
Assess each normal task by:
- number of clicks;
- elapsed time;
- number of manually entered values;
- number of navigation changes;
- need for external documentation;
- need for terminal or configuration editing;
- recovery effort after failure.

Prefer the smallest safe change that produces the largest measurable reduction in User Effort Score.

## Primary product surfaces
### Operational home
When a verified usable camera exists, video is the operational home and receives the largest useful area. Health and next action remain glanceable without displacing video.

The FPV workspace may show video and a live map side by side or let the operator switch between them. The map shows the drone's observed position, direction of travel and travelled track. It may also show the Starlink terminal's location when supplied by the connected terminal/API. Drone and terminal positions are distinct observations and must include their source and freshness. Never infer either position from an IP address or stale cached coordinates.

The map must identify stale or unavailable position data rather than presenting it as live. Track history is drawn only from fresh observed drone coordinates. Provide cached/offline map availability where the chosen map source permits it, and make any retained location history visible and controllable by the operator.

Support multiple displays as part of the FPV workspace. Operators can move a video stream to another monitor by dragging it or using an explicit “Move to display” action, detach it into a window, and return it to the main workspace without restarting the stream. Offer clear presets such as video + map, two vehicle workspaces, and one stream per display; keep labels and device status visible in every detached window. Restore a saved layout only when its display arrangement is unambiguous. If a monitor disconnects, move its stream back to the main workspace and explain what happened.

Controllers are assigned to vehicle/flight-controller operation sessions, not directly to cameras. A vehicle session may reference one or more cameras; each controller-to-vehicle assignment must remain visible and unambiguous. Multiple independent vehicle sessions can be presented in one station, with explicit focus and separate video, map, telemetry, controller and health state.

The operator can preserve the OSD already present in the incoming aircraft video. Station-generated OSD is an independent overlay with separate controls: keep the original video OSD, show the station OSD, or show both with a non-overlapping layout. The safe default never modifies or attempts to remove the source OSD. If source OSD is burned into the video pixels, disabling the station overlay must not imply that the source OSD was removed.

Station OSD settings are available from Home and Service mode, persist automatically, and allow corner placement, text scaling, background opacity and reset to defaults. Provide a preview that is clearly identified as layout-only, with no fabricated live telemetry; make settings easy to reach before video operation and keep editing out of the active flight view.

### Connectivity and Starlink
Show separate evidence for Starlink terminal state, mobile 4G/5G availability, the station's active network route, video, telemetry and control. A connected terminal or available Internet route does not by itself prove that the aircraft, video, telemetry or control channel is usable. Show the active and available backup route only when observed; do not claim automatic failover unless it is implemented and verified for the supported network equipment.

Starlink management belongs in a dedicated Connectivity/Starlink surface, with a compact persistent status on the FPV workspace. Supported status and controls depend on the verified terminal/router model and its available interface. Do not invent capabilities when a model does not expose them.

During a Starlink update or reboot, keep a visible status through the full transition: update in progress, reboot required, rebooting, waiting for reconnection, online again, or failed. Warn before an action that can interrupt the network. After reconnection, independently revalidate the network route, video, telemetry and control evidence before showing the station as ready.

### Preflight readiness
Provide a concise readiness check for each vehicle session. Summarize observed controller assignment/input freshness, camera/video, telemetry, network route, position freshness and OSD source. Show what is ready, what needs attention and what remains unknown, with one useful next action. Do not infer readiness from one component's connected state, and do not invent hardware-specific thresholds.

### Alerts and session history
Prioritize alerts by their observed impact. Critical alerts remain visible without covering the central video; non-critical updates are quiet and deduplicated until the state changes. Use text and iconography as well as color, and never hide an unresolved critical state behind an acknowledgement.

Keep a human-readable session timeline for meaningful connection changes, stale/lost/restored video or telemetry, Starlink update/reboot states, device discovery and operator-confirmed configuration changes. Provide a sanitized export and clear retention controls for location and session history.

### Health Dashboard
First-run, disconnected and recovery states show a compact health surface that answers within 10 seconds:
- Is the system ready?
- What is working?
- What needs attention?
- What should I do now?

Use the common vocabulary only:
- `ready`: normal operation can continue;
- `attention`: user input or a non-critical prerequisite is needed;
- `problem`: normal operation is blocked or degraded;
- `unknown`: evidence is insufficient.

Do not convert unknown evidence into a guessed score. A percentage may be displayed only when its calculation is deterministic, understandable and tested.

### Device Center
Show supported cameras, vehicles/flight controllers and operator controllers in one discoverable place while preserving their separate physical identities.

For each device show a human name, type, observed version when available, health and last observed activity. Group automatically. Do not expose transport implementation as separate devices.

### Timeline
Replace raw logs in normal UI with chronological human events such as application started, configuration applied, device found, backup created, update started and verification completed.

Raw logs and correlation evidence remain available only in technical details or Service Mode.

### Next Best Action
Normal UI emphasizes at most one primary contextually useful action. Examples: find device, connect, show video, calibrate controller, diagnose, apply a known safe fix, update, restore backup, or no action needed.

The engine must respect all safety boundaries. Destructive actions remain deliberate and explicit.

## Core platform boundaries
The core platform consists of:
- Health Engine;
- Device Manager;
- Discovery Engine;
- Timeline Engine;
- Smart Search Engine;
- Next Best Action Engine;
- Backup Engine;
- Plugin Host;
- Update Manager;
- Settings Manager;
- Human Message Layer.

Device, service and plugin implementations emit normalized evidence. Health interprets evidence. Human Message Layer explains it. Next Best Action selects the safest useful response. UI consumes presentation models rather than raw exceptions or protocol states.

## Discovery and identity
After launch, scan bounded trustworthy sources for supported USB, COM/serial, network devices and local services. New devices should appear without restarting the application.

Discovery remains route-aware and bounded. Generic reachability is not proof of device identity. A remembered address is a candidate, not fresh hardware evidence. Manual IP is fallback after automatic discovery or restore has not produced a usable device.

## Plugins
New device families should integrate through versioned plugin contracts rather than changes to core workflow code. A plugin describes identity, vendor, version, capabilities, discovery hooks, health hooks and presentation metadata.

Plugins may contribute normalized evidence and safe actions. They may not bypass common health vocabulary, human-message policy, secret boundaries, backup policy or destructive-action gates.

## Backup and recovery
Create an automatic backup before every critical reversible configuration change. Recovery must be available as one clear action when safe.

Backups must be identity-bound, versioned and validated before restore. Failed or ambiguous restore remains blocked and explained in human language.

## Offline operation
Basic local operation must not require an account or cloud service. Keep local device/controller profiles and workspace layouts available offline. Use cached maps when supported by the selected provider, and make it clear when map tiles or remote device capabilities are unavailable.

## Smart search and in-app assistance
Search accepts natural task language and routes the user to the relevant action or surface. It should answer task questions, not expose internal file or component names.

AI assistance is a later advisory layer over sanitized structured evidence. It may explain and suggest, but never becomes authority for identity, telemetry, compatibility, credentials, ownership, firmware success, destructive approval or execution.

## Progressive disclosure
Normal mode contains only information and actions needed for the current task.

Advanced contains manual network/transport choices, stream options, protocol detail, controller mapping detail and expanded diagnostic evidence.

Service Mode contains recovery/fullflash, manual firmware, low-level configuration, developer diagnostics and Hardware E2E validation.

Hardware E2E is mandatory evidence for physical claims but is not a normal operator feature.

## Safety and evidence
UX convenience never overrides safety. Software CI, simulators, mocks, cached state and cloud metadata never count as physical hardware evidence.

Destructive firmware operations require current observed device identity, compatibility, verified artifact integrity, session authentication, explicit approval and post-operation verification. Successful dispatch means reboot pending, not successful update.

## First-run acceptance contract
A release candidate must demonstrate the integrated journey:

`install -> launch -> automatic discovery/restore -> health -> devices -> next action -> usable operation`

Normal acceptance requires:
- first understandable state in less than 10 seconds under defined test conditions;
- no configuration-file editing;
- no terminal requirement;
- manual IP only as fallback;
- no raw technical errors in normal UI;
- at most one primary next action;
- a recovery route for every blocked normal state;
- physical evidence for hardware-dependent success claims.

Missing acceptance evidence is not success.

## Definition of Done
A product change is complete only when:
- its user scenario and acceptance evidence are defined;
- the default path minimizes User Effort Score;
- safe automatic detection or derivation is used;
- user-facing failures use human language;
- Next Best Action is present where action is needed;
- critical reversible changes are protected by backup;
- meaningful events appear in Timeline;
- negative and recovery paths are tested;
- documentation is not required for the normal path;
- CI or physical evidence supports every completion claim.

## Product success criterion
A first-time user installs and launches FPV Uhyliant, understands system state, sees available devices and completes all basic actions without documentation, configuration editing or technical knowledge.

If this is not true, the gap is a product defect and receives priority according to user impact.