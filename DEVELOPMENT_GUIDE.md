# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Baseline
Windows ground station: Python + PySide6 + Qt Quick/QML. Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode. FPV remains video-first. Target stacks: ArduPilot, Betaflight, INAV. Target protocols: MAVLink, MSP, CRSF.

## Rules
- New telemetry/control backends begin read-only; unknown/stale/missing state is unavailable.
- Camera presets and stream video profiles are separate. Firmware never applies video profiles.
- Generic ONVIF/name hints are not OpenIPC evidence.
- Recovery/fullflash is only for verified compatible existing custom OpenIPC.
- Destructive writes require verified compatibility, explicit approval and observed verification.

## Current architecture
Telemetry, firmware, dual-video/PiP, camera-preset and read-only external-navigation/link diagnostic foundations are implemented software-side. Hardware-dependent validation remains pending.

Station backup now has a versioned, integrity-checked export and a non-mutating import inspection path. The snapshot preserves devices, streams, per-stream video profiles, verified OpenIPC identity and active-device selection as distinct entities. Import inspection must validate schema version, SHA-256 and referential integrity before any restore can be considered.

Do not treat backup integrity as confidentiality. Current portable backup JSON is not encrypted. Do not add silent restore: applying imported state requires an explicit user decision and must eventually be transactional. Pairing secrets and private signing keys must never be included in portable station snapshots.

## Next work
1. Validate hardware-dependent paths on real target devices when hardware is available.
2. Add encrypted backup envelope and explicit transactional restore.
3. Add station pairing and distribution hardening without committing private keys.

## Workflow
Inspect actual `main`, test software paths, mark hardware-only validation `hardware-validation-pending`, synchronize canonical docs after material changes and never claim CI/write success without evidence.
