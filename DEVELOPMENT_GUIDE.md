# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Baseline
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Target stacks: ArduPilot, Betaflight, INAV. Target protocols: MAVLink, MSP, CRSF.

## Core rules
- Unknown/stale/missing telemetry and diagnostics remain unavailable.
- Camera presets, stream video profiles and firmware are separate entities.
- Generic ONVIF/name hints are not verified OpenIPC evidence.
- Recovery/fullflash is not a generic install path.
- Private signing keys and pairing secrets are never committed or exported in station snapshots.

## Backup/restore security boundary
Portable station backup v3 uses `cryptography` AES-256-GCM with a password-derived scrypt key. The envelope metadata required to interpret the ciphertext is authenticated as AES-GCM associated data. Do not add unauthenticated envelope fields that affect decryption/restore semantics.

Snapshot validation is strict and allow-listed: exact entity fields, scalar types/ranges, unique IDs/names/device-kind pairs, host/port uniqueness, active-device membership, stream-to-device/profile references and verified OpenIPC identity references must pass before restore. Unknown fields are rejected so future secret-bearing state is not silently imported.

Import remains two-phase. Inspection decrypts/authenticates and validates, but does not mutate live state. Restore requires explicit confirmation and uses a single SQLite transaction. Never add silent restore, partial replacement, signing keys or pairing secrets to portable snapshots.

## Current architecture
Telemetry, guarded firmware lifecycle, dual-video/PiP, camera presets, read-only link diagnostics, authenticated encrypted backup and transactional restore are implemented software-side. Hardware validation remains pending where noted in `PROJECT_STATE.md`.

## Next work
1. Hardware validation when target devices are available.
2. Station pairing with OS-protected secret storage and explicit trust/revocation lifecycle.
3. Continue installer/update distribution hardening without committing private keys.

## Workflow
Inspect actual `main`, test software paths, synchronize canonical docs after material changes, and never claim CI/write success without evidence.
