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
Portable station backup v2 requires a password of at least eight characters. `station_backup.py` derives independent encryption/authentication material with scrypt, encrypts the serialized snapshot, and authenticates the complete envelope metadata plus ciphertext before decrypting. This is a dependency-free application format, not a claim of platform-backed secret storage; moving to an established AEAD implementation remains preferred when dependency policy permits it.

Import is two-phase. Inspection only decrypts/authenticates, validates schema and referential integrity, and retains an in-memory pending snapshot. Restore requires explicit confirmation. The confirmed database replacement is one SQLite transaction; exceptions roll it back. Never add silent restore, partial table replacement, or import of signing/pairing secrets.

## Current architecture
Telemetry, guarded firmware lifecycle, dual-video/PiP, camera presets, read-only link diagnostics, encrypted backup export and transactional restore are implemented software-side. Hardware validation remains pending where noted in `PROJECT_STATE.md`.

## Next work
1. Hardware validation when target devices are available.
2. Station pairing with OS-protected secret storage and explicit trust lifecycle.
3. Distribution hardening and migration of portable backup encryption to a vetted AEAD dependency when available.

## Workflow
Inspect actual `main`, test software paths, synchronize canonical docs after material changes, and never claim CI/write success without evidence.
