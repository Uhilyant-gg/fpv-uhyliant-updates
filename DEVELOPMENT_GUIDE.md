# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Product / UI
Windows ground station using Python + PySide6 + Qt Quick/QML. Core flow: Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode. FPV remains video-first.

## Non-negotiable rules
- Target flight stacks: ArduPilot, Betaflight, INAV; protocols: MAVLink, MSP, CRSF.
- New telemetry/control backends begin read-only; unknown/stale/missing telemetry is unavailable.
- Camera preset and video profile are separate entities. Video profile belongs to a stream and must never be silently applied by firmware flashing.
- Generic ONVIF/name hints are not OpenIPC evidence. OpenIPC hardware fields are populated only from observed verified evidence.
- Primary installation, upgrade and recovery/fullflash are separate paths. Recovery/fullflash is only for verified compatible existing custom OpenIPC and is not a generic primary installer.
- Before destructive firmware writes: identify hardware and flash layout, validate profile compatibility, verify image integrity, preserve a recovery path, bind the approval to immutable inputs, re-hash before write, reboot/rediscover and verify after operation.
- Never commit private signing keys; release metadata is immutable and signed.

## Current architecture
Telemetry uses normalized providers behind `TelemetryRouter`; FPV consumes one vehicle-level contract. MSP serial polling is read-only and CRSF serial receive is passive. Real telemetry hardware validation remains `hardware-validation-pending`.

OpenIPC discovery persists verified identity separately in SQLite. Video runtime carries stream-aware RTSP diagnostics. Firmware Center supports SSC30KQ / IMX335 compatibility checks, SHA-256 artifact verification, immutable pre-check approval and non-destructive per-mode execution-plan generation. No destructive hardware executor is attached yet.

Versioned camera presets have a compatibility boundary and are explicitly separate from per-stream video profiles.

## Next work
1. Define executor interfaces and operation-state/locking contracts for primary, upgrade and recovery/fullflash without enabling generic destructive flashing.
2. Re-verify artifact SHA-256 immediately before any future executor handoff.
3. Define rediscovery/post-operation verification contract.
4. Improve stream metadata and diagnostics (main/sub, codec, resolution, FPS, latency/playback state) and prepare secondary/thermal/PiP.
5. Expand camera presets separately from video profiles.
6. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
7. Add encrypted DB export/import, station pairing and continue updater/installer/frozen-build hardening.

## Development workflow
Inspect current `main` before changes. Keep software tests moving while marking hardware-only validation `hardware-validation-pending`. Update both canonical docs after material architecture changes. Do not claim CI/write success without confirmation. Preserve failure diagnostics and release/update security behavior.
