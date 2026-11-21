# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. Target controllers: ArduPilot, Betaflight, INAV. Target telemetry protocols: MAVLink, MSP, CRSF. Video and telemetry remain separate runtimes.

## MAVLink phase 1: code complete, hardware validation pending
The phase-1 backend is strictly read-only. It exposes no ARM/DISARM, mode change, parameter write, message request or vehicle-control command.

Implemented:
- configurable UDP/TCP/serial endpoint and baud, persisted with QSettings;
- quick endpoint presets plus optional system/component filtering;
- passive FC identity from HEARTBEAT and passive AUTOPILOT_VERSION parsing when broadcast;
- heartbeat/connection, armed, mode, battery voltage/current/remaining, GPS fix/satellites/HDOP, altitude, ground speed, heading, roll/pitch/yaw, RSSI and home distance;
- freshness windows that invalidate stale telemetry instead of displaying old values as live;
- link health state, rolling message rate, last-packet age, received/BAD_DATA counters and diagnostic sequence-gap loss estimate;
- RADIO_STATUS diagnostics when broadcast plus SYS_STATUS communication errors/controller load;
- reusable `MavlinkDiagnostics.qml` integrated in telemetry and diagnostics popups;
- JSON diagnostics export to the local FPV-Uhyliant data directory;
- backend startup self-test without a real FC and packaged backend smoke-test.

Important: sequence-gap packet loss is diagnostic only and can over-report loss when routers or redundant links alter which packets reach the GCS. Real-FC validation is still required before declaring the phase field-validated.

## Existing foundation
- Windows PyInstaller/OTA/release pipeline and packaged GUI smoke-test.
- SQLite devices, streams and video profiles.
- OpenIPC discovery through mDNS, ONVIF hints, fingerprinting and bounded /24 probing.
- separate RTSP VideoRuntime.
- maximum-video-workspace flight screen.

## Camera preset vs video profile
Camera preset is device/firmware configuration. Video profile belongs to a stream. Video profile is not applied as part of a camera flash.

## OpenIPC flashing rule
BAT/fullflash is only for cameras already running a compatible custom OpenIPC setup. Future provisioning must identify hardware/flash layout, validate compatibility, back up state, verify images and provide recovery before destructive writes.

## Next implementation order
1. Hardware-validate MAVLink phase 1 against a real FC and long-running link.
2. Harden VideoRuntime reconnect/stall diagnostics.
3. Introduce vehicle-level model and structured diagnostics engine.
4. Add safe OpenIPC provisioning and versioned camera presets.
5. Add normalized telemetry providers, then read-only MSP and CRSF.
6. Add StabX/external-navigation and Starlink/VPN diagnostics.
7. Add encrypted database export/import and station pairing.

## Acceptance rule
No decorative telemetry in production UI. Unknown, absent or stale values are unavailable. New protocol backends begin read-only.
