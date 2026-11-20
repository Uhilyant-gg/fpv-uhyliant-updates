# FPV Uhyliant development guide

This file and `PROJECT_STATE.md` are the canonical persistent handoff/context for future development chats. Read both from current `main` before making changes. Update both whenever project state, blockers, architecture decisions, release behavior, priorities, or the development plan materially change. Do not let either file become a historical snapshot that contradicts current `main`.

## Product goal

`ФПВ Ухилянт` is a Windows ground-station application for FPV systems. The application should provide one coherent workflow for discovering devices, configuring cameras/video, installing OpenIPC firmware, diagnostics, FPV operation, updates, and later flight-controller telemetry/control integration.

## Core UI flow

Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode

Firmware should also be directly reachable in the context of a camera:

Devices -> Camera -> Firmware

## Current technology baseline

- Python + PySide6.
- Qt Quick/QML UI.
- Qt Multimedia video playback.
- SQLite persistence for devices, streams, settings, and video profiles.
- Windows per-user installation.
- OTA update flow with signed manifests, SHA-256 package integrity, Ed25519 signatures, launcher startup verification, and rollback.
- GitHub Actions builds Windows packages/releases.

## Non-negotiable architecture rules

1. `src/` is authoritative source.
2. Camera preset and video profile are separate entities.
3. Video profile belongs to a camera/video stream and is not applied during camera flashing.
4. A camera or each of its streams may have its own video profile.
5. BAT/fullflash is not the universal primary OpenIPC installation method. It is intended only for cameras already running the relevant custom OpenIPC firmware.
6. OpenIPC installation should be automated as far as safely possible.
7. Generic ONVIF devices must not be classified as OpenIPC without actual OpenIPC/Majestic evidence.
8. Target flight stacks are ArduPilot, Betaflight, and INAV.
9. Target protocols include MAVLink, MSP, and CRSF.
10. Published release metadata under `releases/<version>/` is immutable.
11. Never commit private signing keys.
12. Every published release requires a signed manifest, SHA-256 metadata, and Git tag.

## Immediate release priority: 2.0.10

The current blocker is reliable startup validation of the packaged Windows application.

Current 2.0.10 work includes:

- explicit PySide6.QtMultimedia inclusion in the PyInstaller build;
- packaged GUI/QML smoke testing;
- `startup.log` for unhandled startup exceptions;
- `qt-startup.log` for Qt/QML/Multimedia messages;
- marker-based smoke testing so GUI initialization failure can be distinguished from shutdown hangs;
- full signing/publishing/Pages release pipeline preserved;
- Inno Setup fallback version aligned to 2.0.10.

Observed CI history relevant to the current blocker:

1. The original packaged smoke test timed out while waiting for the GUI process to exit.
2. Marker-based validation was introduced.
3. A later run exited with `-1` before creating the smoke marker.
4. Current `main` uses a single quoted PowerShell argument line for `--smoke-test --smoke-marker <path>` and prints available startup/Qt diagnostics into the failed CI job.

Do not move the release forward while packaged GUI/QML validation is failing. Diagnose the actual failure first and keep the diagnostic evidence.

Expected installed runtime diagnostics directory:

`%LOCALAPPDATA%/FPV-Uhyliant`

Important diagnostic files may include:

- `startup.log`
- `qt-startup.log`
- `startup-ok.json`
- `updater.log`

CI also uses `smoke-test-ok.json` as the explicit successful-GUI-initialization marker.

## Development priority after 2.0.10 is validated

### P0. Firmware Center first

Firmware has priority over further video/telemetry development because real OpenIPC hardware is needed to validate the downstream camera functionality.

Target entry point:

Devices -> Camera -> Firmware

Target workflow:

Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify

Initial real hardware target should include the SSC30KQ / IMX335 OpenIPC setup already used during manual flashing/recovery work.

The Firmware Center should eventually identify as much of the following as the hardware exposes:

- IP / hostname
- platform / SoC
- sensor
- current firmware/OpenIPC state
- Majestic availability
- supported installation/recovery path

Keep primary installation, upgrade, and recovery/fullflash paths clearly separated.

### P1. OpenIPC device integration

After flashing works, make an OpenIPC camera a first-class manageable device rather than only a discovered IP address.

Expected camera page areas:

- identity/platform/sensor
- firmware state
- network state
- Majestic/OpenIPC state
- streams
- diagnostics
- Firmware action

### P2. Real video validation

Then harden the path required for actual FPV video:

- automatic RTSP stream detection
- main/sub stream support
- reconnect behavior
- playback error diagnostics
- codec/resolution/FPS visibility where available
- latency diagnostics
- stream switching
- fullscreen
- later secondary/thermal stream and PiP

Do not treat a successful TCP connection to port 554 as proof that RTSP playback is healthy.

### P3. Camera presets and video profiles

Keep these models independent.

Conceptual model:

Camera -> Camera preset

Camera -> Stream 1 -> Video profile A

Camera -> Stream 2 -> Video profile B

Video profiles should cover stream/playback-oriented settings such as codec, FPS, bitrate, resolution, and latency mode where applicable.

### P4. Flight-controller integration

Add read-only integration first, then configuration/write operations later.

Support targets:

- ArduPilot via MAVLink
- Betaflight via MSP/CRSF as appropriate
- INAV via MSP/CRSF as appropriate

The first objective is reliable discovery/connection and telemetry ingestion, not parameter editing.

### P5. FPV Mode and OSD

Combine verified video and flight telemetry into FPV Mode.

Potential OSD/status areas include:

- flight mode
- battery/power
- GPS/navigation quality including HDOP where available
- link/network state
- Starlink/network connectivity state where measurable
- external navigation/stabilization state when exposed by an integration
- warnings and failsafe state

Do not invent telemetry. Display only values actually received from the connected system.

## Development workflow

1. At the start of a new development chat, read current `DEVELOPMENT_GUIDE.md` and `PROJECT_STATE.md` from `main` before proposing or applying changes.
2. Inspect the actual current source files related to the requested change before writing.
3. After every material change to state, blockers, roadmap, architecture, release behavior, or workflow, update both canonical context files in the same development cycle.
4. `PROJECT_STATE.md` should answer: what is true right now, what is blocked, what was most recently changed, and what should happen next.
5. `DEVELOPMENT_GUIDE.md` should answer: what are we building, what rules must remain true, and in what priority/order should functionality be implemented.
6. Small corrective changes may be committed directly to `main` when appropriate, per the current user preference.
7. Risky/substantial changes should use focused review and CI before merge.
8. Preserve existing release/update/security behavior unless the change explicitly targets it.
9. Do not merge or publish failing validation.
10. For release-pipeline changes, ensure signing/publishing/Pages jobs remain present.
11. For Windows GUI changes, validate the frozen executable, not only Python source execution.
12. When diagnostics fail, preserve or upload useful logs/artifacts instead of replacing the error with a generic timeout.
13. Firmware changes must not silently apply video profiles.

## Definition of done for the next major milestone

The next major milestone is not simply a Firmware button. It is reached when, on a supported test camera, the application can identify the device, choose the appropriate supported OpenIPC firmware path, execute the intended flashing workflow with safeguards, reboot/rediscover the camera, and verify that the resulting OpenIPC/Majestic system is reachable. Real video validation follows immediately after that.
