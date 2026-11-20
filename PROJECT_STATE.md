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
- Windows installer pipeline: implemented

## v2.0.3 hotfix

- Fix OTA package URL generation in `automated-ota.yml`.
- Generate the GitHub Pages base URL at workflow runtime from `GITHUB_REPOSITORY_OWNER` and `GITHUB_REPOSITORY` rather than storing a literal release-host URL in workflow source.
- Validate generated package URLs before signing: HTTPS is required, hostname must exist, and placeholder angle brackets are rejected.
- Synchronize application/runtime metadata to `2.0.3`.
- Preserve production Ed25519 signing through GitHub secret `FPV_RELEASE_PRIVATE_KEY`, package SHA-256 verification, startup-OK and rollback.

## Known issues / validation needed

- v2.0.2 manifest published a malformed package hostname and cannot download its OTA ZIP from the client.
- v2.0.3 signed OTA requires CI publication and real-PC validation from installed v2.0.1.
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

- Publish and validate signed v2.0.3 OTA on the `test` channel.
- Validate Windows installer on a real station PC.
- Real RTSP/OpenIPC video backend and future secondary/thermal source/PiP.
- Read-only MAVLink telemetry backend for ArduPilot/Pixhawk/CubeOrangePlus.
- Persistent OSD positions, visibility, scale and profiles.
- Network diagnostics for latency, loss, jitter, TX/RX and Starlink/WireGuard/link state.
- Map/GNSS presentation and documented R2D2/OpenIPC read-only telemetry/overlay integration.
