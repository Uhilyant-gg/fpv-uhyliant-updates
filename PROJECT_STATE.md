# FPV Uhyliant project state

## Current baseline

- Current source version: `2.0.3`
- Release channel: `test`
- UI: PySide6 + Qt Quick/QML
- Update repository: GitHub Pages
- Manifest path: `test/release.json`
- Signing key ID: `fpv-uhyliant-production-v1`
- Package integrity: SHA-256
- Manifest authentication: Ed25519
- Atomic update: implemented
- Startup-OK handshake: implemented
- Rollback: implemented

## Unified release pipeline

- `automated-ota.yml` is the authoritative release pipeline.
- One run validates source/version and rejects committed private signing keys.
- It builds the OTA ZIP, calculates SHA-256, creates and validates the package URL, signs the manifest with `secrets.FPV_RELEASE_PRIVATE_KEY`, and verifies the signed channel.
- A Windows job builds `FPV-Uhyliant.exe`, smoke-tests it, builds `FPV-Uhyliant-Setup-<version>.exe`, and hashes the installer.
- A publish job commits signed OTA artifacts, creates the version tag, creates/updates the GitHub Release, and attaches OTA + Setup assets.
- The same workflow prepares a GitHub Pages artifact and a dependent deploy job publishes it.
- Standalone `release.yml`, `pages.yml`, and `windows-installer.yml` are retired to avoid duplicate release/deployment paths.
- `verify.yml` remains as independent repository validation for normal source changes.

## v2.0.3 hotfix

- Fixed the malformed package-host incident from v2.0.2.
- Package URL generation occurs inside CI and is validated before Ed25519 signing.
- Production private key remains outside the repository and is materialized only from GitHub Actions secret `FPV_RELEASE_PRIVATE_KEY`.

## Known issues / validation needed

- Installed v2.0.1 still needs real-PC OTA validation against the published v2.0.3 Pages manifest.
- Video, MAVLink telemetry, network diagnostics, map, persistent OSD profiles and STABX telemetry remain planned integrations.
- STABX telemetry protocol must be based on documentation or observed telemetry format before implementation.

## Repository rules

1. `src/` is the authoritative source tree.
2. Every release gets its own immutable folder under `releases/<version>/`.
3. Channel manifests only point to a release package.
4. Private signing keys must never be committed.
5. Every release must include a changelog and SHA256SUMS.txt.
6. Every published version must have a Git tag.

## Next work

- Validate v2.0.3 OTA from installed v2.0.1.
- Validate unified pipeline end-to-end on the next version bump.
- Real RTSP/OpenIPC video backend and future secondary/thermal source/PiP.
- Read-only MAVLink telemetry backend for ArduPilot/Pixhawk/CubeOrangePlus.
- Persistent OSD positions, visibility, scale and profiles.
- Network diagnostics for latency, loss, jitter, TX/RX and Starlink/WireGuard/link state.
- Map/GNSS presentation and documented R2D2/OpenIPC read-only telemetry/overlay integration.
