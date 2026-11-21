# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Product/UI baseline
Windows ground station: Python + PySide6 + Qt Quick/QML. Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode. FPV remains video-first.

## Non-negotiable rules
- ArduPilot, Betaflight, INAV; MAVLink, MSP, CRSF.
- New telemetry/control backends begin read-only. Unknown/stale/missing state is unavailable.
- Camera presets and video profiles are separate; video profiles belong to streams and are not applied by firmware flashing.
- Generic ONVIF/name hints do not establish OpenIPC.
- Primary, upgrade and recovery/fullflash are distinct. Recovery/fullflash is only for verified compatible existing custom OpenIPC.
- Destructive writes require observed hardware/layout compatibility, verified image, recovery path, immutable approval, pre-handoff re-hash, operation lock, reboot/rediscovery and observed post-operation verification.

## Current architecture
Telemetry uses normalized providers behind `TelemetryRouter`; FPV consumes one vehicle contract. Real telemetry validation is `hardware-validation-pending`.

OpenIPC identity persistence and stream-aware RTSP diagnostics exist. Stream profile metadata may supply codec/resolution/FPS/latency-mode, while endpoint-connect timing is only a reachability diagnostic.

Firmware Center has SSC30KQ / IMX335 compatibility, SHA-256 verification, immutable approval and guarded executor lifecycle. Hardware adapters remain disabled by default. Executor captures pre-operation identity and verifies a structured observed post-reboot identity through the post-flash verifier before declaring success. Real device observation is `hardware-validation-pending`.

Versioned camera presets are independent of per-stream video profiles.

## Next work
1. Add real hardware adapters only for explicitly validated mechanisms; never use generic fullflash fallback.
2. Continue stream switching/playback diagnostics and secondary/thermal/PiP preparation without synthesizing metadata.
3. Expand camera presets without coupling them to stream profiles.
4. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
5. Add encrypted DB export/import, station pairing and distribution hardening.

## Workflow
Inspect actual `main`, test software paths, mark hardware-only checks `hardware-validation-pending`, keep canonical docs synchronized after material changes, and never claim CI/write success without evidence.
