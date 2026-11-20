# FPV Uhyliant project state

Read this file together with `DEVELOPMENT_GUIDE.md` before making changes. These two files are the canonical handoff for new development chats and must be updated whenever project state, blockers, architecture decisions, release behavior, priorities, or the development plan materially change.

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

## Current 2.0.10 release blocker

The Windows binaries build successfully, but packaged GUI/QML startup validation remains the active gate before publishing/validating 2.0.10 on the target Windows PC.

Smoke-test diagnostics identified the concrete startup failure: `QQmlApplicationEngine` could not load `Main.qml` because the QML parser reported `Unexpected token ';'` at lines 13 and 22. This proves the Windows Qt platform plugin was found and loaded, while QML parsing prevented creation of the root object.

Current `main` includes a direct fix to `src/app/Main.qml` that changes affected signal handlers to explicit block bodies and removes parser-ambiguous semicolon boundaries around those handlers. The next required action is to re-run the 2.0.10 Windows release pipeline from current `main` and inspect the packaged smoke-test result.

Current smoke-test contract:

1. Start the frozen `FPV-Uhyliant.exe` with `--smoke-test --smoke-marker <path>`.
2. Successful QML root creation writes `smoke-test-ok.json`.
3. The test requests window close and `app.exit(0)`.
4. CI treats absence of the marker as GUI/QML initialization failure.
5. A shutdown hang after successful marker creation is reported separately and the process may be terminated by CI.
6. Diagnostics are preserved/uploaded when available.

Expected diagnostics under `%LOCALAPPDATA%/FPV-Uhyliant` during a normal installed run include:

- `startup.log` for unhandled Python startup exceptions
- `qt-startup.log` for Qt/QML/Multimedia messages
- `startup-ok.json` for launcher startup verification
- `updater.log` for launcher/update events

CI smoke testing also uses `smoke-test-ok.json` as its explicit initialization marker.

## Version 2.0.10 changes

- Windows frozen build explicitly imports `PySide6.QtMultimedia` and collects its PyInstaller package data/plugins.
- CI validates the packaged GUI/QML application rather than relying only on the Python-only `--self-test`.
- Packaged smoke testing is marker-based.
- Qt/QML/Multimedia startup diagnostics are captured.
- QML parser errors found by packaged smoke testing have been corrected in `Main.qml` and require CI re-validation.
- Full release pipeline retains Windows build, signing/publishing, and Pages deployment stages.
- Inno Setup fallback version is `2.0.10`.
- Firmware behavior remains unchanged by the 2.0.10 startup hotfix work.

## Next validation

1. Re-run the `2.0.10` Windows release pipeline from current `main` after the `Main.qml` parser fix.
2. If smoke test fails, inspect the exact QML/Qt diagnostics before making further changes.
3. Publish/build the test installer only after packaged GUI/QML initialization succeeds.
4. Install the test EXE on the target Windows PC.
5. Validate normal launcher startup, OTA/startup verification, and rollback behavior.
6. Firmware Center work may be developed in parallel, but 2.0.10 remains gated on packaged startup validation.

## Development priority after 2.0.10

P0 is `Devices -> Camera -> Firmware` because a working OpenIPC camera is required for meaningful downstream validation.

Target firmware workflow:

`Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify`

Initial real hardware focus includes SSC30KQ / IMX335.

After Firmware Center:

1. OpenIPC camera identity/state integration.
2. Real RTSP stream detection and playback hardening.
3. Camera presets and per-stream video profiles while keeping those models separate.
4. Read-only flight-controller integration for ArduPilot, Betaflight, and INAV using MAVLink/MSP/CRSF as appropriate.
5. FPV Mode, telemetry, and OSD.

## Project rules

1. `src/` is authoritative source.
2. `DEVELOPMENT_GUIDE.md` and `PROJECT_STATE.md` are the canonical project handoff/context and must stay current.
3. Release metadata under `releases/<version>/` is immutable after publication.
4. Private signing keys must never be committed.
5. Every published release must have signed manifest, SHA-256 metadata and Git tag.
6. Camera presets and video profiles are separate models.
7. Video profiles are assigned per camera/video stream and are never applied as part of camera flashing.
8. BAT/fullflash is only for cameras already running the relevant OpenIPC firmware, not the universal primary flashing path.
9. Generic ONVIF devices must not be classified as OpenIPC without OpenIPC/Majestic evidence.
10. Target flight stacks/protocols include ArduPilot, Betaflight, INAV and MAVLink/MSP/CRSF.
11. Primary UI flow: Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode.
12. Small corrective changes may be committed directly to `main` when appropriate; risky or substantial changes should use focused review/CI before merge.
13. Do not move a release forward while its packaged Windows validation is failing.
