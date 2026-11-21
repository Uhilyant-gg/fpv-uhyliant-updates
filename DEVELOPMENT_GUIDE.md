# FPV Uhyliant development guide

This file and `PROJECT_STATE.md` are the canonical persistent handoff/context for future development chats. Read both from current `main` before making changes. Update both whenever project state, blockers, architecture decisions, release behavior, priorities, or the development plan materially change.

## Product goal
`ФПВ Ухилянт` is a Windows ground-station application for FPV systems, combining device discovery, camera/video management, OpenIPC firmware operations, diagnostics, FPV operation, updates and flight-controller telemetry in one workflow.

## Core UI flow
Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode

Firmware is also reachable in camera context:
Devices -> Camera -> Firmware

## Technology baseline
- Python + PySide6.
- Qt Quick/QML UI.
- Qt Multimedia video playback.
- SQLite devices, streams, settings and video profiles.
- Windows per-user installation.
- OTA with signed manifests, SHA-256 integrity, Ed25519 signatures, launcher verification and rollback.
- GitHub Actions Windows builds/releases.

## Non-negotiable architecture rules
1. `src/` is authoritative source.
2. Camera preset and video profile are separate entities.
3. Video profile belongs to a camera/video stream and is not applied during camera flashing.
4. A camera or each stream may have its own video profile.
5. BAT/fullflash is only for cameras already running the relevant compatible custom OpenIPC firmware, not a universal install method.
6. OpenIPC installation should be automated as far as safely possible.
7. Generic ONVIF devices must not be classified as OpenIPC without OpenIPC/Majestic evidence.
8. Target flight stacks are ArduPilot, Betaflight and INAV.
9. Target protocols include MAVLink, MSP and CRSF.
10. Published release metadata under `releases/<version>/` is immutable.
11. Never commit private signing keys.
12. Every published release requires a signed manifest, SHA-256 metadata and Git tag.
13. New flight protocol backends start read-only.
14. Do not display invented or stale telemetry as live.
15. Protocol-specific parsing belongs below the normalized telemetry-provider boundary; FPV UI consumes the vehicle model rather than duplicating protocol-specific telemetry UI.

## Current development state
MAVLink phase 1 and the normalized vehicle/diagnostics foundation exist. Read-only MSP and passive CRSF parsing/runtime foundations now also exist behind normalized providers, with software tests. The app is still wired to MAVLink by default, so MSP/CRSF transport and provider selection remain integration work. All real FC/radio validation is hardware-validation-pending and must not block software-only progress.

RTSP recovery/diagnostics exist but still require real OpenIPC validation.

## Current implementation order
### P0. Protocol integration
Add safe provider selection and serial transport/device handling for MSP and CRSF, while keeping new paths read-only and preserving a single vehicle/UI model.

### P1. Vehicle model and diagnostics
Continue strengthening structured diagnostics so telemetry, video, network and external-navigation health share consistent unavailable/stale/error semantics.

### P2. Safe OpenIPC provisioning
Target workflow:
Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify

Initial supported hardware should include SSC30KQ / IMX335. Keep primary installation, upgrade and recovery/fullflash paths separate. Before destructive writes, identify hardware/flash layout, validate compatibility, preserve a recovery path and verify images.

### P3. OpenIPC device integration and video
Make OpenIPC cameras first-class devices with verified identity/platform/sensor, firmware, network, Majestic state, streams and diagnostics. Continue stream discovery, main/sub streams, codec/resolution/FPS visibility where available, latency diagnostics, stream switching, fullscreen and preparation for secondary/thermal/PiP. TCP port reachability is not proof of healthy RTSP playback.

### P4. Presets and profiles
Keep versioned camera presets separate from per-stream video profiles. Video profiles must not silently participate in firmware flashing.

### P5. StabX and network integration
Add external-navigation/StabX status only through a verified supported interface, plus Starlink/VPN/link diagnostics. Feed only verified received status into FPV OSD and diagnostics.

### P6. Distribution and persistence
Add encrypted database export/import and station pairing, then continue frozen executable, installer, updater, signed OTA and rollback validation.

## Development workflow
1. Read current `DEVELOPMENT_GUIDE.md` and `PROJECT_STATE.md` from `main` before work.
2. Inspect actual current source and recent commits before editing.
3. Update both canonical context files after material state/architecture/roadmap changes.
4. Do not publish failing validation or claim CI success without evidence.
5. Small corrective changes may go directly to `main`; risky/substantial changes should receive focused review and CI before merge.
6. Preserve release/update/security behavior unless explicitly changing it.
7. For Windows GUI changes, validate the frozen executable, not only source execution.
8. Preserve useful failure logs/artifacts.
9. Firmware changes must not silently apply video profiles.
10. Mark hardware-only verification as hardware-validation-pending and continue software-testable work.
