# FPV Uhyliant project state

## Current baseline

- Current source version: `2.0.2`
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
- Windows installer pipeline: implemented; v2.0.2 requires CI and real-PC validation

## v2.0.2 work

- Normalize product version and window title to `ФПВ Ухилянт 2.0.2`.
- Use one Python version module as the client runtime version source.
- Keep production public key in the client; private key remains only in GitHub Actions secret `FPV_RELEASE_PRIVATE_KEY`.
- Primary Windows user asset: `FPV-Uhyliant-Setup-2.0.2.exe`.
- Preserve test-channel Ed25519/SHA-256 OTA, startup-OK and rollback.
- Optimize Windows packaging conservatively without removing required Qt Quick/QML runtime components.

## Known issues / validation needed

- v2.0.2 Windows installer and OTA require CI build and real-PC validation after source changes.
- Video, MAVLink telemetry, network diagnostics, map, persistent OSD profiles and STABX telemetry are planned integrations, not production implementations yet.
- STABX telemetry protocol must be based on documentation or observed telemetry format before implementation.

## Repository rules

1. `src/` is the authoritative source tree.
2. Every release gets its own immutable folder under `releases/<version>/`.
3. Channel manifests only point to a release package.
4. Private signing keys must never be committed.
5. Every release must include a changelog and SHA256SUMS.txt.
6. Every published version must have a Git tag.

## Next work

- Validate v2.0.2 Windows installer and signed OTA on a real station PC.
- Real RTSP/OpenIPC video backend, including future secondary/thermal source and PiP.
- Read-only MAVLink telemetry backend for ArduPilot/Pixhawk/CubeOrangePlus.
- Persistent OSD element positions, visibility, scale and profiles.
- Network diagnostics for latency, loss, jitter, TX/RX, Starlink/WireGuard/link state.
- Map and GNSS presentation.
- R2D2/OpenIPC read-only telemetry/overlay integration where documented.
