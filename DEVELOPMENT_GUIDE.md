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

Video now has a `StreamWorkspace` above playback. It chooses only real persisted enabled streams, supports primary/secondary selection and swapping, and only reports PiP available with two distinct real streams. Playback remains a single active `VideoRuntime`; secondary simultaneous decoding/rendering is not yet implemented. Stream diagnostics can show associated profile codec/resolution/FPS/latency-mode and endpoint reachability timing.

Versioned camera presets remain independent from video profiles.

## Next work
1. Add a secondary playback runtime/render path and PiP state without compromising main-video workspace priority.
2. Add playback-health/frame-stall instrumentation supported by Qt observations; do not infer glass-to-glass latency.
3. Expand camera presets independently.
4. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
5. Add encrypted DB export/import, station pairing and distribution hardening.

## Workflow
Inspect actual `main`, test software paths, mark hardware-only validation `hardware-validation-pending`, synchronize canonical docs after material changes and never claim CI/write success without evidence.
