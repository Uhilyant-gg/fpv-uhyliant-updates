# FPV Uhyliant development guide

This file is the persistent handoff/context for future development chats. Read this file together with `PROJECT_STATE.md` before making changes.

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

The current blocker is reliable startup of the packaged Windows application.

2.0.10 changes include:

- explicit PySide6.QtMultimedia inclusion in the PyInstaller build;
- packaged GUI/QML smoke testing;
- `startup.log` for unhandled startup exceptions;
- `qt-startup.log` for Qt/QML/Multimedia messages;
- marker-based smoke testing so GUI initialization failure can be distinguished from shutdown hangs.

Do not move the release forward when the packaged GUI/QML validation is failing. Diagnose the failure first.

Expected runtime diagnostics directory:

`%LOCALAPPDATA%/FPV-Uhyliant`

Important diagnostic files may include:

- `startup.log`
- `qt-startup.log`
- `startup-ok.json`
- `smoke-test-ok.json` during smoke testing
- `updater.log`

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

For non-trivial changes:

1. Inspect current `main` before writing.
2. Preserve existing release/update/security behavior unless the change explicitly targets it.
3. Prefer a focused branch and PR for risky changes.
4. Run CI before merge.
5. Do not merge a failing CI change.
6. For release-pipeline changes, ensure the signing/publishing/Pages jobs remain present.
7. For Windows GUI changes, validate the frozen executable, not only Python source execution.
8. When diagnostics fail, preserve or upload useful logs/artifacts instead of replacing the error with a generic timeout.
9. Firmware changes must not silently apply video profiles.
10. After each meaningful milestone, update this file and `PROJECT_STATE.md` so a new development chat can recover context from the repository itself.

## Definition of done for the next major milestone

The next major milestone is not simply a Firmware button. It is reached when, on a supported test camera, the application can identify the device, choose the appropriate supported OpenIPC firmware path, execute the intended flashing workflow with safeguards, reboot/rediscover the camera, and verify that the resulting OpenIPC/Majestic system is reachable. Real video validation follows immediately after that.
