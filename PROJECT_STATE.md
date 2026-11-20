# FPV Uhyliant project state

## Current baseline

- Source version: `2.0.9`
- Product name: `ФПВ Ухилянт`
- Release channel: `test`
- UI: PySide6 + Qt Quick/QML + Qt Multimedia
- Manifest path: `test/release.json`
- Signing key ID: `fpv-uhyliant-production-v1`
- Package integrity: SHA-256
- Manifest authentication: Ed25519
- Per-user Windows install path: `%LOCALAPPDATA%\Programs\FPV Uhyliant`
- Windows layout: launcher + updater helper + `app/current`
- Runtime/user data: `%LOCALAPPDATA%/FPV-Uhyliant`

## Version 2.0.9 checkpoint

- Devices persistence uses SQLite with legacy `devices.json` migration.
- SQLite schema includes devices, streams, settings and independent video profiles.
- Each stream can have its own video profile assignment.
- OpenIPC discovery uses mDNS, ONVIF, Majestic/OpenIPC fingerprinting and bounded `/24` probing with network-interface selection.
- RTSP stream runtime and Qt Multimedia playback are integrated into the UI.
- Diagnostics exposes basic RTSP runtime state/error information.

## Validation gate

1. Publish `2.0.9` through `.github/workflows/automated-ota.yml` on the test channel.
2. Validate OTA install/startup and rollback behavior.
3. Validate legacy Devices -> SQLite migration on Windows.
4. Validate discovery with real OpenIPC and generic ONVIF devices.
5. Validate persistent per-stream video profile assignment.
6. Validate real OpenIPC RTSP playback, stop/start and error handling.

## Next development after validation

1. Harden RTSP/OpenIPC diagnostics and stream discovery.
2. OpenIPC camera integration and maximally automated firmware workflow.
3. Camera presets remain separate from video profiles.
4. Add read-only ArduPilot/Betaflight/INAV integration using MAVLink/MSP/CRSF as appropriate.
5. Extend OSD, network diagnostics, secondary/thermal video and PiP.

## Project rules

1. `src/` is authoritative source.
2. Release metadata under `releases/<version>/` is immutable after publication.
3. Private signing keys must never be committed.
4. Every published release must have signed manifest, SHA-256 metadata and Git tag.
5. Camera presets and video profiles are separate models.
6. Video profiles are assigned per camera/video stream and are never applied as part of camera flashing.
7. BAT/fullflash is only for cameras already running the relevant OpenIPC firmware, not the universal primary flashing path.
8. Generic ONVIF devices must not be classified as OpenIPC without OpenIPC/Majestic evidence.
9. Target flight stacks/protocols include ArduPilot, Betaflight, INAV and MAVLink/MSP/CRSF.
10. Primary UI flow: Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode.
