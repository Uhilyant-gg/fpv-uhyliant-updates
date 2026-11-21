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

## Current development state
MAVLink phase 1 is implemented in read-only form and awaits real FC/long-running-link validation. The RTSP runtime now has explicit reconnect/stalled/error state handling and the UI has bounded automatic recovery plus manual reconnect/diagnostic visibility. Both areas still require real-hardware validation.

## Current implementation order
### P0. Hardware validation
Validate MAVLink phase 1 against a real flight controller and exercise RTSP playback/recovery against real OpenIPC hardware. Preserve diagnostics from failures.

### P1. Vehicle model and diagnostics
Introduce a vehicle-level model above individual telemetry transports and a structured diagnostics engine so MAVLink, later MSP/CRSF, video, network and external-navigation health can be represented consistently.

### P2. Safe OpenIPC provisioning
Target workflow:
Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify

Initial supported hardware should include the SSC30KQ / IMX335 OpenIPC setup used during manual flashing/recovery work. Keep primary installation, upgrade and recovery/fullflash paths separate. Before destructive writes, identify hardware/flash layout, validate compatibility, preserve recoverable state and verify images.

### P3. OpenIPC device integration and video
Make OpenIPC cameras first-class devices with identity/platform/sensor, firmware, network, Majestic state, streams and diagnostics. Continue real-video work including stream discovery, main/sub streams, codec/resolution/FPS visibility where available, latency diagnostics, stream switching, fullscreen and later secondary/thermal/PiP. TCP port reachability is not proof of healthy RTSP playback.

### P4. Presets and profiles
Keep camera preset separate from per-stream video profiles. Video profiles cover playback/stream-oriented settings and must not silently participate in firmware flashing.

### P5. Protocol normalization
After the vehicle/diagnostics abstraction exists, add normalized providers and then read-only MSP and CRSF support for Betaflight/INAV while retaining MAVLink support for ArduPilot.

### P6. StabX and network integration
Add external-navigation/StabX status integration when exposed by a supported interface, plus Starlink/VPN/link diagnostics. Feed only verified received status into FPV OSD and diagnostics.

## Development workflow
1. Read current `DEVELOPMENT_GUIDE.md` and `PROJECT_STATE.md` from `main` at the start of development work.
2. Inspect actual current source before editing.
3. Update both canonical context files after material changes to state, blockers, roadmap, architecture, release behavior or workflow.
4. `PROJECT_STATE.md` records what is true now and what happens next.
5. `DEVELOPMENT_GUIDE.md` records product rules and development order.
6. Small corrective changes may go directly to `main` when appropriate.
7. Risky/substantial changes should receive focused review and CI before merge.
8. Preserve existing release/update/security behavior unless explicitly changing it.
9. Do not publish failing validation.
10. For Windows GUI changes, validate the frozen executable, not only source execution.
11. Preserve useful failure logs/artifacts.
12. Firmware changes must not silently apply video profiles.

## Next major milestone
The next milestone requires real-hardware evidence: stable MAVLink telemetry on a supported FC and reliable RTSP playback/recovery on a supported OpenIPC camera. After that, vehicle-level diagnostics and safe provisioning can be built on validated foundations.
