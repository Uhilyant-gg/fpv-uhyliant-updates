# FPV Uhyliant product and UX principles

## Primary rule
Minimize operator effort while maximizing useful automation. Complexity stays hidden until it is needed.

## Default journey
The normal path should feel like: launch -> discover/connect -> video -> operate.

When something fails, prefer: problem -> diagnose -> safe fix.

Advanced and Service Mode exist for cases that cannot be handled safely by the normal path.

## Zero-config first
Automatic discovery, identification, capability detection, stream selection and safe defaults are preferred. Manual IP addresses, ports, protocol details and other technical controls belong in Advanced unless required for the current task.

## Video first
The video workspace gets the largest useful area. Persistent UI contains only information and controls needed during operation. Secondary controls belong in contextual popups, drawers or detail views.

## Device-centered model
Present a camera or controller as one device rather than exposing transport implementation details as separate concepts. Device details may expose Video, Status, Settings, Firmware and Diagnostics when relevant.

## Progressive disclosure
Normal mode stays simple and task-oriented. Expert mode may expose IP addresses, ports, RTSP details, telemetry internals, firmware identity, evidence and logs. Service Mode contains recovery and other specialist workflows.

## Actionable health
Use a small common health vocabulary: ready, attention, problem and unknown. Unknown remains unknown and must never be converted into guessed telemetry or device identity.

User-facing failures describe the practical problem first. Technical error details remain available on demand.

## Contextual actions
Prefer the next useful action to a large permanent toolbar. Examples include Add after discovery, Open video after configuration, Update when a compatible update is verified, Diagnose on failure, and Fix only when the application has a known safe remediation.

## Safe automation
A one-click fix is appropriate only for deterministic, non-destructive remediation. Destructive operations continue through their existing validation and approval boundaries. AI diagnosis is advisory and never bypasses those boundaries.

## Firmware experience
The normal firmware path should reduce to a clear update offer and a deliberate Update action when compatibility is verified. Catalog selection, download integrity, device binding, reboot and post-update verification remain internal unless intervention is required. Recovery/fullflash stays separate from normal update.

## Diagnostics
Diagnostics should run with minimal operator effort and explain the practical fault before technical evidence. Diagnostic exports are sanitized and preserve unknown values. The same structured bundle may later support AI-assisted diagnosis.

## UI quality rule
Do not expose dead controls. If an action is unavailable, explain why and, where known, what prerequisite is missing.

## Product decision test
For every visible feature ask: does this make the operator faster, safer, or make the situation clearer? If not, hide it from the default workflow or remove it.
