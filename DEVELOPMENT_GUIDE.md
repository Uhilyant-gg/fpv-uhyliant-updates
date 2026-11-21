# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Baseline
Windows ground station: Python + PySide6 + Qt Quick/QML. Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode. FPV remains video-first. Target stacks: ArduPilot, Betaflight, INAV. Target protocols: MAVLink, MSP, CRSF.

## Rules
- New telemetry/control backends begin read-only; unknown/stale/missing state is unavailable.
- Camera presets and stream video profiles are separate. Firmware never applies video profiles.
- Generic ONVIF/name hints are not OpenIPC evidence.
- Primary/upgrade/recovery-fullflash are separate. Recovery/fullflash is only for verified compatible existing custom OpenIPC.
- Destructive writes require verified compatibility, image/recovery/layout gates, immutable approval, pre-handoff re-hash, locking, reboot/rediscovery and observed post-operation verification.

## Current architecture
Telemetry provider integration and MSP/CRSF serial foundations exist; hardware validation remains pending.

Firmware Center and guarded executor lifecycle reach the real-hardware boundary. No adapter is enabled by default. Post-flash identity can be verified from a structured observation, but acquiring real observations is `hardware-validation-pending`.

Video uses `StreamWorkspace` for real persisted selection and `VideoWorkspaceRuntime` for lifecycle. The runtime owns isolated primary/secondary `VideoRuntime` objects. QML binds them to independent `MediaPlayer`/`VideoOutput` pairs. PiP is permitted only when primary and secondary are distinct real streams. PiP off stops the secondary decoder/runtime; disconnect stops both; swap restarts playback using only the selected persisted stream IDs.

Playback health must remain observational: Qt playing/stopped/error signals plus runtime reconnect/stall transitions, attempts and last-event timestamps are allowed. Do not invent decoded FPS, dropped frames, glass-to-glass latency or other values Qt/runtime did not provide. Profile metadata is configuration metadata, and endpoint check time is reachability only.

Versioned camera presets remain independent from video profiles.

## Next work
1. Validate simultaneous decoder/render and recovery behavior on target Windows hardware (`hardware-validation-pending`).
2. Expand camera presets independently.
3. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
4. Add encrypted DB export/import, station pairing and distribution hardening.

## Workflow
Inspect actual `main`, test software paths, mark hardware-only validation `hardware-validation-pending`, synchronize canonical docs after material changes and never claim CI/write success without evidence.
