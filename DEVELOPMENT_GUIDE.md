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
- SQLite devices, streams, settings, verified OpenIPC identity and video profiles.
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
7. Generic ONVIF devices and name hints must not be classified as OpenIPC without verified OpenIPC/Majestic evidence.
8. Target flight stacks are ArduPilot, Betaflight and INAV.
9. Target protocols include MAVLink, MSP and CRSF.
10. Published release metadata under `releases/<version>/` is immutable.
11. Never commit private signing keys.
12. Every published release requires a signed manifest, SHA-256 metadata and Git tag.
13. New flight protocol backends start read-only.
14. Do not display invented or stale telemetry as live.
15. Protocol-specific parsing belongs below the normalized telemetry-provider boundary; FPV UI consumes the vehicle model rather than duplicating protocol-specific telemetry UI.
16. OpenIPC platform/SoC, sensor, firmware and Majestic fields remain empty unless actually observed from verified evidence.

## Current development state
MAVLink phase 1 and the normalized vehicle/diagnostics foundation exist. Read-only MSP and passive CRSF parsing/runtime foundations exist behind normalized providers, with serial transports, persistent provider selection and software tests. FPV OSD consumes the selected normalized provider. All real FC/radio validation is hardware-validation-pending and must not block software-only progress.

OpenIPC discovery now distinguishes generic ONVIF candidates from verified OpenIPC devices and persists normalized verified identity separately in SQLite schema version 4. Platform/SoC, sensor, firmware and Majestic version are retained only when observed. Real SSC30KQ / IMX335 validation remains hardware-validation-pending.

RTSP recovery/diagnostics exist but still require real OpenIPC validation.

## Current implementation order
### P0. Protocol integration
Software integration of provider selection and unavailable semantics is complete enough to move forward; keep MAVLink/MSP/CRSF read-only and maintain one vehicle/UI contract. Real hardware validation remains hardware-validation-pending.

### P1. Vehicle model and diagnostics
Continue strengthening structured diagnostics so telemetry, video, network and external-navigation health share consistent unavailable/stale/error semantics.

### P2. Safe OpenIPC provisioning
Target workflow:
Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify

Initial supported hardware should include SSC30KQ / IMX335. Keep primary installation, upgrade and recovery/fullflash paths separate. Before destructive writes, identify hardware/flash layout, validate compatibility, preserve a recovery path and verify images.

### P3. OpenIPC device integration and video
Verified OpenIPC identity persistence exists. Next expose verified identity, main/sub streams and diagnostics in the device UI. Continue stream discovery, codec/resolution/FPS visibility where available, latency diagnostics, stream switching, fullscreen and preparation for secondary/thermal/PiP. TCP port reachability is not proof of healthy RTSP playback.

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
