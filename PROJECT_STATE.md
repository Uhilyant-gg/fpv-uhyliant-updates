# FPV Uhyliant project state

`main` is the single source of truth for implementation. Historical chat snippets must not replace newer repository code.

## Product direction
FPV Uhyliant is a Windows ground-station application focused on a maximum-video-workspace flight view. Target controller/protocol coverage remains ArduPilot, Betaflight and INAV with MAVLink, MSP and CRSF. Protocol integrations stay isolated from video.

## Implemented foundation
- Windows PyInstaller build, launcher/update helper and GitHub release/OTA pipeline.
- Packaged GUI/QML and MAVLink backend smoke tests.
- SQLite-backed devices, streams and video profiles.
- OpenIPC discovery via mDNS, ONVIF hints, fingerprinting and bounded /24 probing.
- Separate RTSP `VideoRuntime` and read-only `MavlinkRuntime`.
- Maximum-video-workspace flight screen with popup configuration.

## MAVLink phase 1
The backend is read-only and exposes no ARM/DISARM, mode change, parameter write or vehicle-control command.

Telemetry includes heartbeat, armed state, mode, battery, GPS, position, speed, heading, attitude, RSSI and home distance. Values are invalidated when stale.

Identity is learned passively from the flight-controller HEARTBEAT: system/component IDs, vehicle type, autopilot type, system state and MAVLink field version. If the FC broadcasts AUTOPILOT_VERSION, firmware, board, vendor/product, UID and capabilities are recorded. No request command is sent.

Link diagnostics include rolling message rate, last-packet age, received/bad packet counts, estimated sequence-gap loss per source, top message types, SYS_STATUS communication errors/load, and RADIO_STATUS RSSI/noise/error/buffer fields when broadcast. `MavlinkDiagnostics.qml` provides a reusable identity/link diagnostics view.

## Camera preset vs video profile
Camera preset is device/firmware configuration. Video profile is stream configuration. A video profile is not applied during camera flashing and each stream can select its own profile.

## OpenIPC flashing rule
BAT/fullflash is only for cameras already running a compatible custom OpenIPC setup. Future provisioning must identify hardware and flash layout, validate compatibility, back up state, verify images and provide recovery before destructive writes.

## Next implementation order
1. Validate MAVLink identity/link diagnostics against a real FC and packaged Windows build.
2. Integrate the reusable diagnostics view into the consolidated diagnostics popup and add export.
3. Harden video reconnect, stall detection and diagnostics.
4. Introduce a vehicle-level model and structured diagnostics engine.
5. Add safe OpenIPC provisioning and versioned camera presets.
6. Add normalized providers, then read-only MSP and CRSF.
7. Add StabX/external-navigation health and Starlink/VPN diagnostics.
8. Add encrypted database export/import and station pairing.

## Acceptance rule
No decorative telemetry in production UI. Unknown, absent or stale values remain unavailable. New protocol backends begin read-only.
