# FPV Uhyliant project state

## Current baseline

- Source version: `2.0.8`
- Product name: `ФПВ Ухилянт`
- Release channel: `test`
- UI: PySide6 + Qt Quick/QML
- Manifest path: `test/release.json`
- Signing key ID: `fpv-uhyliant-production-v1`
- Package integrity: SHA-256
- Manifest authentication: Ed25519
- Per-user Windows install path: `%LOCALAPPDATA%\Programs\FPV Uhyliant`
- Windows layout: launcher + updater helper + `app/current`
- Atomic application switch, startup-OK handshake and automatic rollback: implemented
- Runtime/user data: `%LOCALAPPDATA%/FPV-Uhyliant`

## Version 2.0.8 scope

- Hardened OpenIPC discovery and device database validation.
- Safe discovery cancellation and QThread cleanup.
- Hardened OTA manifest/package validation.
- Atomic `.part`, `ready.json` and `launcher-state.json` handling.
- Parallel updater operations are blocked.
- ZIP path and symbolic-link validation is enforced.
- CI now compiles Python sources, runs application self-test, checks version consistency, verifies signed test metadata and rejects private signing keys.

## Devices module

- Persistent local device database is implemented in `%LOCALAPPDATA%/FPV-Uhyliant/devices.json`.
- Saved devices support active-device selection, editing and deletion.
- OpenIPC discovery combines mDNS, ONVIF WS-Discovery, Majestic/OpenIPC fingerprinting and bounded local `/24` probing.
- Results are merged by address and restricted to the selected network interface.
- Confirmed OpenIPC devices are distinguished from unconfirmed network/ONVIF devices.
- Unconfirmed devices cannot be saved as OpenIPC cameras through discovery.
- Discovery reports its current stage, progress, result count, cancellation, completion and errors.

## OTA/update foundation

- The updater fetches the signed test-channel manifest.
- Manifest authenticity is verified with Ed25519 using key ID `fpv-uhyliant-production-v1`.
- Package integrity is verified with SHA-256.
- Update installation can be blocked when the autopilot is armed, recording is active, or streaming is active.
- The packaged update helper installs outside the running application process.

## Current validation gate

1. Publish `2.0.8` through `.github/workflows/automated-ota.yml`.
2. Validate `2.0.7 -> 2.0.8` using OTA only.
3. Confirm the update completes without Setup.exe and without UAC.
4. Validate signature and SHA-256 verification, self-test, atomic switch, restart and startup-OK handling.
5. Validate automatic rollback with a controlled failed-startup test.
6. Validate Devices discovery and cancellation on Windows with real OpenIPC and generic ONVIF cameras.
7. Confirm that unverified ONVIF devices cannot be saved as OpenIPC cameras.

## Product roadmap after OTA validation

1. Real OpenIPC camera integration and camera configuration controls.
2. Persistent video profiles with per-stream assignment and editing.
3. Real RTSP/OpenIPC video backend, then secondary/thermal source and PiP.
4. Read-only MAVLink telemetry for ArduPilot/Pixhawk/CubeOrangePlus.
5. Persistent OSD positions, visibility, scale and profiles.
6. Network diagnostics for latency, loss, jitter, TX/RX and Starlink/WireGuard/link state.
7. CRSF, R2D2/OpenIPC and STABX telemetry/overlay integration.
8. Map/GNSS presentation and local-first pilot data.

## Project rules

1. `src/` is authoritative source.
2. Release metadata under `releases/<version>/` is immutable after publication.
3. Private signing keys must never be committed.
4. Every release must have a signed manifest, SHA-256 metadata and Git tag.
5. Video profiles remain independent from camera flashing/configuration presets.
6. The BAT/fullflash method is only for cameras already running the relevant custom OpenIPC firmware.
7. Generic ONVIF devices must not be classified as OpenIPC without OpenIPC/Majestic evidence.
