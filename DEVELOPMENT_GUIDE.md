# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Baseline
Windows ground station: Python + PySide6 + Qt Quick/QML. Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode. FPV remains video-first. Target stacks: ArduPilot, Betaflight, INAV. Target protocols: MAVLink, MSP, CRSF.

## Rules
- New telemetry/control backends begin read-only; unknown/stale/missing state is unavailable.
- Camera presets and stream video profiles are separate. Firmware never applies video profiles.
- Generic ONVIF/name hints are not OpenIPC evidence.
- Primary/upgrade/recovery-fullflash are separate; recovery/fullflash is only for verified compatible existing custom OpenIPC.
- Destructive writes require verified compatibility, immutable approval and observed post-operation verification.

## Current architecture
Telemetry provider integration and MSP/CRSF serial foundations exist; hardware validation remains pending. Firmware Center and guarded executor lifecycle reach the real-hardware boundary; no adapter is enabled by default.

Video uses `StreamWorkspace` plus `VideoWorkspaceRuntime` with isolated primary/secondary `VideoRuntime` objects and independent Qt render paths. PiP requires distinct real streams. Playback health is observational only; do not synthesize decoded FPS, dropped frames or glass-to-glass latency.

Camera presets are separate versioned device/camera settings requiring verified OpenIPC platform and sensor identity. Hardware application remains pending a verified device-specific executor.

`LinkDiagnostics` is the read-only boundary for external-navigation and data-link observations. External navigation and network state are separate contracts. Unknown fields stay unavailable; observations age to stale; RTT may be shown only if a real observer supplies it. Do not infer StabX health from generic telemetry, do not infer Starlink status from Internet access, and do not call RTT video latency. No control path is introduced here.

## Next work
1. Validate camera-preset execution and simultaneous video paths on real SSC30KQ / IMX335 Windows hardware (`hardware-validation-pending`).
2. Add verified hardware/protocol observers feeding `LinkDiagnostics` for StabX/external navigation and Starlink/WireGuard when evidence is available.
3. Add encrypted DB export/import, station pairing and distribution hardening.

## Workflow
Inspect actual `main`, test software paths, mark hardware-only validation `hardware-validation-pending`, synchronize canonical docs after material changes and never claim CI/write success without evidence.
