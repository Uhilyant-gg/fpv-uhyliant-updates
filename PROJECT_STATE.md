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
- Runtime/user data: `%LOCALAPPDATA%/FPV-Uhyliant`

## Current UI foundation

- Main station UI is implemented in PySide6 + Qt Quick/QML.
- Application starts maximized and supports F11 fullscreen mode.
- Test video state is available through the UI and F2 shortcut.
- Station menu includes Devices, Video Profiles, Diagnostics, Station Updates and OSD controls.
- Video profile selection UI foundation is implemented.
- Video profiles remain separate from camera flashing/configuration presets.
- Telemetry and real video backends are not implemented yet.

## Devices module

- Persistent local device database is implemented in `%LOCALAPPDATA%/FPV-Uhyliant/devices.json`.
- Saved devices support active-device selection and deletion.
- Saved device fields can be edited: name, IP/hostname, port and notes.
- OpenIPC discovery combines mDNS, ONVIF WS-Discovery, Majestic/OpenIPC fingerprinting and bounded local `/24` probing.
- Discovery results are merged by address.
- Confirmed OpenIPC devices are distinguished from unconfirmed network/ONVIF devices.
- Unconfirmed devices cannot be added to the database as OpenIPC cameras through the discovery action.
- Detailed discovery information includes IP, hostname, confirmation state, discovery sources/services and evidence used for OpenIPC identification.
- Discovery exposes the current stage: `mDNS -> ONVIF -> fingerprint -> /24`.
- The `/24` stage reports completed and total probe counts.
- The UI reports the current number of discovered devices.
- Discovery status reports scanning, cancellation, completion or error.
- Discovery can be cancelled cooperatively; already collected results are retained.

## OTA/update foundation

- The updater fetches the test-channel manifest.
- Manifest authenticity is verified with Ed25519 using key ID `fpv-uhyliant-production-v1`.
- Downloaded OTA packages are verified with SHA-256 before being marked ready.
- Update installation can be blocked by the station safety guard when the autopilot is armed, recording is active, or streaming is active.
- The packaged update helper is used to perform installation outside the running application process.
- The per-user installation introduced in 2.0.7 is intended to allow future OTA updates without administrator elevation.

## Next validation gate

1. Prepare and publish `2.0.8` through the existing release pipeline.
2. Validate `2.0.7 -> 2.0.8` using OTA only.
3. Confirm the update completes without Setup.exe and without UAC.
4. Validate manifest signature verification and OTA package SHA-256 verification.
5. Validate application self-test, atomic switch, restart and startup-OK handling.
6. Validate automatic rollback with a controlled failed-startup test.
7. Validate Devices discovery on Windows with real OpenIPC and generic ONVIF cameras.
8. Validate discovery cancellation during mDNS, ONVIF and `/24` stages.
9. Validate that unconfirmed ONVIF devices are not saved as OpenIPC cameras.

## Product roadmap after OTA validation

- Implement real OpenIPC camera integration and camera configuration controls.
- Implement persistent video profiles and per-stream assignment/editing.
- Real RTSP/OpenIPC video backend and future secondary/thermal source/PiP.
- Read-only MAVLink telemetry backend for ArduPilot/Pixhawk/CubeOrangePlus.
- CRSF-related integration for supported camera/flight-controller workflows.
- Persistent OSD positions, visibility, scale and profiles.
- Network diagnostics for latency, loss, jitter, TX/RX and Starlink/WireGuard/link state.
- Local-first pilot data with Station ID and text pairing/transfer keys; optional encrypted sync relay only.
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
7. Discovery must not classify a generic ONVIF camera as OpenIPC without OpenIPC/Majestic evidence.
