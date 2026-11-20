# FPV Uhyliant project state

## Current bootstrap baseline

- Source version: `2.0.5`
- Release channel: `test`
- UI: PySide6 + Qt Quick/QML
- Manifest path: `test/release.json`
- Signing key ID: `fpv-uhyliant-production-v1`
- Package integrity: SHA-256
- Manifest authentication: Ed25519
- Windows layout: launcher + updater helper + `app/current`
- Atomic application switch: implemented
- Startup-OK handshake: implemented
- Automatic rollback: implemented
- Local updater log: `%LOCALAPPDATA%/FPV-Uhyliant/updater.log`

## v2.0.5 bootstrap goals

- Remove the malformed literal manifest hostname from the application and construct the test-channel manifest URL at runtime.
- Keep the large Windows OTA ZIP in GitHub Release assets rather than normal Git history.
- Validate OTA ZIP SHA-256 before installation.
- Run the packaged application self-test before switching `app/current`.
- Require the self-test version to equal the requested update version.
- Preserve the previous application under `app/rollback/previous` until startup-OK succeeds.
- Verify startup-OK token and version before accepting a new release.
- Roll back automatically when startup verification fails.
- Log updater/launcher transitions locally for field diagnostics.
- Keep user/runtime data under `%LOCALAPPDATA%/FPV-Uhyliant` outside the replaceable `app/current` tree.

## Release architecture

- `.github/workflows/automated-ota.yml` is the authoritative unified release pipeline.
- The pipeline builds the Windows application, launcher, update helper, OTA ZIP and Setup.exe.
- OTA manifest is signed from GitHub Actions secret `FPV_RELEASE_PRIVATE_KEY`.
- Git stores lightweight release metadata only; large binaries are GitHub Release assets.
- GitHub Pages publishes the signed channel manifest.
- Standalone release/pages/installer workflows are retired.

## Validation gate

1. Install `2.0.5` once via Setup.exe because `2.0.4` contains the malformed manifest URL.
2. Publish a minimal `2.0.6` OTA proof release.
3. Validate `2.0.5 -> 2.0.6`: manifest check, Ed25519, download, SHA-256, install button, self-test, atomic switch, automatic restart and startup-OK.
4. Validate rollback with a controlled failed-startup test before declaring the OTA foundation stable.

## Product roadmap after OTA validation

- Real RTSP/OpenIPC video backend and future secondary/thermal source/PiP.
- Read-only MAVLink telemetry backend for ArduPilot/Pixhawk/CubeOrangePlus.
- Persistent OSD positions, visibility, scale and profiles.
- Network diagnostics for latency, loss, jitter, TX/RX and Starlink/WireGuard/link state.
- Local-first device/pilot database with Station ID and text pairing/transfer keys; optional encrypted sync relay only.
- Map/GNSS presentation.
- Documented R2D2/OpenIPC and STABX telemetry/overlay integration.

## Repository rules

1. `src/` is authoritative source.
2. Release metadata is immutable under `releases/<version>/` after publication.
3. Private signing keys must never be committed.
4. Every release must carry a signed manifest and SHA-256 metadata.
5. Every published version must have a Git tag.
