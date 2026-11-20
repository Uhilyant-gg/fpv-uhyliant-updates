# FPV Uhyliant project state

## Current baseline

- Source version: `2.0.7`
- Product name: `ФПВ Ухилянт`
- Release channel: `test`
- UI: PySide6 + Qt Quick/QML
- Manifest path: `test/release.json`
- Signing key ID: `fpv-uhyliant-production-v1`
- Package integrity: SHA-256
- Manifest authentication: Ed25519
- Per-user Windows install path: `%LOCALAPPDATA%\Programs\FPV Uhyliant`
- Windows layout: launcher + updater helper + `app/current`
- Atomic application switch: implemented
- Startup-OK handshake: implemented
- Automatic rollback: implemented
- Local updater log: `%LOCALAPPDATA%/FPV-Uhyliant/updater.log`
- Runtime/user data: `%LOCALAPPDATA%/FPV-Uhyliant`

## Current v2.0.7 UI foundation

- Main station UI is implemented in PySide6 + Qt Quick/QML.
- Application starts maximized and supports F11 fullscreen mode.
- Test video state is available through the UI and F2 shortcut.
- Station menu includes Devices, Video Profiles, Diagnostics, Station Updates and OSD controls.
- Video profile selection UI foundation is implemented.
- Video profiles currently available in the UI: `Мінімальна затримка`, `Збалансований`, `Низький бітрейт`, `Максимальна якість`, `Користувацький`.
- Video profiles are assigned to video streams, not to camera firmware or camera flashing presets.
- Stream targets currently exposed by the UI: `Основний потік`, `Додатковий потік`, `Thermal / PiP`.
- Device database UI is present as a placeholder; adding devices is not implemented yet.
- Diagnostics UI is present as a foundation; quick check and report generation are not implemented yet.
- Telemetry is not configured yet.

## OTA/update foundation

- The updater fetches the test-channel manifest.
- Manifest authenticity is verified with Ed25519 using key ID `fpv-uhyliant-production-v1`.
- Downloaded OTA packages are verified with SHA-256 before being marked ready.
- Update installation can be blocked by the station safety guard when the autopilot is armed, recording is active, or streaming is active.
- The packaged update helper is used to perform installation outside the running application process.
- The per-user installation introduced in 2.0.7 is intended to allow future OTA updates without administrator elevation.

## v2.0.7 migration

1. Install `2.0.7` once using Setup.exe.
2. Use the new Start menu or desktop shortcut.
3. Confirm that the application title shows `2.0.7` and opens maximized.
4. The old Program Files installation may then be removed separately.
5. Runtime data remains under `%LOCALAPPDATA%\FPV-Uhyliant`.

## Next validation gate

1. Publish `2.0.8` through the existing release pipeline.
2. Validate `2.0.7 -> 2.0.8` using OTA only.
3. Confirm the update completes without Setup.exe and without UAC.
4. Validate manifest signature verification and OTA package SHA-256 verification.
5. Validate application self-test, atomic switch, restart and startup-OK handling.
6. Validate automatic rollback with a controlled failed-startup test before declaring the OTA foundation stable.

## Product roadmap after OTA validation

- Implement the persistent local device database for boards, cameras and flight controllers.
- Implement device discovery/connection workflows and active-device state.
- Implement real OpenIPC camera integration and camera configuration controls.
- Keep camera setup/flashing presets separate from video profiles.
- Implement persistent video profiles and per-stream assignment/editing.
- Real RTSP/OpenIPC video backend and future secondary/thermal source/PiP.
- Read-only MAVLink telemetry backend for ArduPilot/Pixhawk/CubeOrangePlus.
- CRSF-related integration for supported camera/flight-controller workflows.
- Persistent OSD positions, visibility, scale and profiles.
- Network diagnostics for latency, loss, jitter, TX/RX and Starlink/WireGuard/link state.
- Local-first device/pilot database with Station ID and text pairing/transfer keys; optional encrypted sync relay only.
- Map/GNSS presentation.
- Documented R2D2/OpenIPC and STABX telemetry/overlay integration.

## Camera and video-profile separation

- Camera firmware/configuration presets and video profiles are separate concepts.
- A camera flashing preset must not contain or apply video-profile settings.
- Video profiles belong to a selected video stream and can be managed independently of camera flashing.
- The existing BAT/fullflash workflow is not the universal camera flashing path; it is a separate method for cameras already running the relevant custom OpenIPC firmware.

## Release architecture

- `.github/workflows/automated-ota.yml` is the authoritative unified release pipeline.
- The pipeline builds the Windows application, launcher, update helper, OTA ZIP and Setup.exe.
- OTA manifest is signed from GitHub Actions secret `FPV_RELEASE_PRIVATE_KEY`.
- Git stores lightweight release metadata only; large binaries are GitHub Release assets.
- GitHub Pages publishes the signed channel manifest.
- Standalone release/pages/installer workflows are retired.

## Repository rules

1. `src/` is authoritative source.
2. Release metadata is immutable under `releases/<version>/` after publication.
3. Private signing keys must never be committed.
4. Every release must carry a signed manifest and SHA-256 metadata.
5. Every published version must have a Git tag.
6. Video-profile settings must remain independent from camera flashing/configuration presets.
