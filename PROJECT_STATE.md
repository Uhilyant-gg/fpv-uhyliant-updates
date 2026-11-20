# FPV Uhyliant project state

## Current baseline

- Source version: `2.0.10`
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

## Version 2.0.10 hotfix

- Windows frozen build explicitly imports PySide6.QtMultimedia and collects its required PyInstaller package data/plugins.
- CI runs a packaged GUI/QML smoke-test instead of relying only on the Python-only self-test.
- Unhandled startup failures are written to `%LOCALAPPDATA%/FPV-Uhyliant/startup.log`.
- Firmware behavior is unchanged by this hotfix.

## Next validation

1. Build `2.0.10` on Windows CI.
2. Verify packaged GUI/QML startup in CI.
3. Install the test EXE on the target Windows PC.
4. Confirm normal startup or inspect `startup.log` if startup fails.
5. Continue camera/firmware work only after the Windows executable is stable.

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
