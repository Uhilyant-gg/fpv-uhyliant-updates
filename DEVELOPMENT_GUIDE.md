# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Product / UI
Windows ground station using Python + PySide6 + Qt Quick/QML. Core flow: Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode. FPV remains video-first.

## Non-negotiable rules
- Target flight stacks: ArduPilot, Betaflight, INAV; protocols: MAVLink, MSP, CRSF.
- New telemetry/control backends begin read-only; unknown/stale/missing telemetry is unavailable.
- Camera preset and video profile are separate. Video profile belongs to a stream and is never silently applied by firmware flashing.
- Generic ONVIF/name hints are not OpenIPC evidence. Hardware fields come only from observed verified evidence.
- Primary, upgrade and recovery/fullflash are separate paths. Recovery/fullflash is only for verified compatible existing custom OpenIPC and is not a generic primary installer.
- Before destructive writes: identify hardware/layout, validate compatibility, verify image, preserve recovery, bind immutable approval, re-hash directly before executor handoff, lock the operation, reboot/rediscover and verify afterward.

## Current architecture
Telemetry uses normalized providers behind `TelemetryRouter`; FPV consumes one vehicle contract. Real telemetry validation is `hardware-validation-pending`.

OpenIPC identity persistence and stream-aware RTSP diagnostics exist. Firmware Center supports SSC30KQ / IMX335 compatibility, SHA-256 verification, immutable approval and per-mode execution plans. `FirmwareExecutor` is a guarded boundary: it re-hashes immediately before handoff, prevents concurrent firmware operations and requires post-operation verification. No hardware adapter is registered by default, therefore destructive writing is disabled and explicitly `hardware-validation-pending`.

Versioned camera presets have a hardware compatibility boundary and remain independent from video profiles.

## Next work
1. Add supported hardware adapters only where the actual installation/upgrade/recovery mechanism is known; never fall back to generic fullflash.
2. Implement rediscovery plus observed post-operation firmware/identity verification.
3. Improve main/sub stream metadata, codec/resolution/FPS and latency/playback diagnostics; prepare secondary/thermal/PiP.
4. Expand camera presets separately from video profiles.
5. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
6. Add encrypted DB export/import, station pairing and distribution hardening.

## Development workflow
Inspect current `main` before changes. Continue software-testable work while hardware-only validation remains `hardware-validation-pending`. Keep canonical docs synchronized after material architecture changes. Never claim CI/write success without confirmation.
