# FPV Uhyliant project state

`main` is the single source of truth for implementation. Historical chat snippets must not replace newer repository code.

## Product direction

FPV Uhyliant is a Windows ground-station application focused on a maximum-video-workspace flight view. The normal flow is Home / device selection -> Connect -> FPV view. Secondary controls belong in popup or slide-out panels rather than a permanent navigation rail.

Target flight-controller/protocol coverage remains ArduPilot, Betaflight and INAV with MAVLink, MSP and CRSF. Protocol integrations should be isolated backends/providers rather than mixed into the video runtime.

## Implemented foundation

- Windows PyInstaller build, launcher/update helper and GitHub release/OTA pipeline.
- Packaged GUI/QML smoke test.
- SQLite-backed devices, streams and video profiles.
- Network-interface selection and OpenIPC discovery via mDNS, ONVIF hints, Majestic/OpenIPC fingerprinting and bounded /24 probing.
- RTSP `VideoRuntime` kept separate from telemetry.
- Device-selection screen and Connect transition into flight workspace.
- Flight view prioritizes `VideoOutput`; stream/profile, diagnostics and configuration live in popups.

## MAVLink phase 1

`src/app/mavlink_runtime.py` is a read-only MAVLink backend. It does not expose ARM/DISARM, flight-mode changes, parameter writes or other vehicle-control commands.

Current telemetry surface:

- heartbeat / connection state
- armed state
- flight mode
- battery voltage, current and remaining percentage
- GPS fix, satellites and HDOP
- altitude, ground speed and heading
- roll, pitch and yaw
- RSSI with source where available
- home distance when both home and current coordinates are known

Connection settings are configurable and persisted. Default is `udpin:0.0.0.0:14550`; serial endpoints use the configured baud rate.

Telemetry now tracks freshness by group. Stale heartbeat, battery, GPS, position, attitude and radio fields are invalidated instead of leaving old values looking live. Heartbeat controls connection state independently from reception of other MAVLink messages.

CI includes a MAVLink backend startup test without simulated FC telemetry and a packaged-backend startup test in addition to the packaged GUI/QML smoke test.

## Camera preset vs video profile

These are separate concepts.

Camera preset is device/firmware configuration. Video profile is stream presentation/encoding configuration. A video profile is not applied as part of camera flashing. Each camera/video stream may select its own video profile.

## OpenIPC flashing rule

The BAT/fullflash workflow is only appropriate for cameras already running a compatible custom OpenIPC setup. It is not the universal primary flashing method. Future provisioning must identify hardware/flash layout, validate compatibility, back up state where possible, verify the image and provide a recovery path before destructive writes.

## Next implementation order

1. Validate the current MAVLink backend and OSD against a real FC and packaged Windows build.
2. Add source-system/component identity and more explicit message-rate/link diagnostics.
3. Harden video reconnect, stall detection and diagnostics without coupling video to telemetry.
4. Introduce a vehicle-level data model above devices/streams.
5. Build a structured diagnostics engine for station/network/camera/video/FC health.
6. Add safe OpenIPC provisioning and versioned camera presets, keeping video profiles separate.
7. Introduce a normalized telemetry-provider API, then add read-only MSP and CRSF providers.
8. Add StabX/external-navigation health as its own telemetry capability rather than treating it as GPS.
9. Add Starlink/VPN connectivity diagnostics and degraded-link handling.
10. Add encrypted export/import and later station pairing for sharing device databases with minimal server dependency.

## Acceptance rule for telemetry work

No decorative telemetry in production UI. Unknown or stale values display as unavailable. New protocol backends begin read-only and must not silently gain vehicle-control operations.
