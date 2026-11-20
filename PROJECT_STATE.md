# FPV Uhyliant project state

## Current baseline

- Current source version: `2.0.0-test`
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

## Repository rules

1. `src/` is the authoritative source tree.
2. Every release gets its own immutable folder under `releases/<version>/`.
3. Channel manifests only point to a release package.
4. Private signing keys must never be committed.
5. Every release must include a changelog and SHA256SUMS.txt.
6. Every published version must have a Git tag.

## Next work

- Real RTSP/OpenIPC video backend.
- Real MAVLink telemetry backend.
- Persistent OSD element positions and profiles.
- Flight-controller OSD pass-through/render mode.
- Real network measurement workers.
- Windows EXE packaging and installer.
