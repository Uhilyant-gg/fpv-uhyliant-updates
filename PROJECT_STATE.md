# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. Target controllers: ArduPilot, Betaflight, INAV. Target telemetry protocols: MAVLink, MSP, CRSF. Video and telemetry remain separate runtimes.

## MAVLink phase 1: code complete, hardware validation pending
The phase-1 backend is strictly read-only. It exposes no ARM/DISARM, mode change, parameter write, message request or vehicle-control command.

Implemented:
- configurable UDP/TCP/serial endpoint and baud, persisted with QSettings;
- passive FC identity and telemetry from received MAVLink messages;
- telemetry freshness and link/MAVLink diagnostics;
- reusable diagnostics UI and JSON diagnostics export;
- backend and packaged smoke tests.

Real-FC validation is still required before declaring the phase field-validated.

## Vehicle and telemetry abstraction
A vehicle-level runtime and structured diagnostics foundation exists. MAVLink now reaches it through a normalized read-only telemetry provider rather than a MAVLink-specific vehicle dependency. Missing source fields remain null/None and unrelated runtime fields are rejected. CI includes a focused telemetry-provider test.

This provider boundary is the foundation for upcoming read-only MSP and CRSF integrations. Hardware validation pending does not block software-only work.

## VideoRuntime status
RTSP runtime tracks checking, ready, playing, reconnecting, stalled and error states, connection attempts and last-event time. Bounded UI recovery and manual reconnect/diagnostics exist. Real-camera validation remains pending.

## Camera preset vs video profile
Camera preset is device/firmware configuration. Video profile belongs to a stream. Video profile is not applied as part of camera flashing.

## OpenIPC flashing rule
BAT/fullflash is only for cameras already running a compatible custom OpenIPC setup. Provisioning must identify hardware/flash layout, validate compatibility and images, preserve a recovery path, then verify after flashing.

## Next implementation order
1. Add read-only MSP provider for Betaflight/INAV on the normalized provider boundary.
2. Add read-only CRSF telemetry and integrate protocol health without duplicate UI.
3. Continue RTSP diagnostics and safe first-class OpenIPC device/provisioning work.
4. Add versioned camera presets separately from per-stream video profiles.
5. Add StabX/external-navigation and Starlink/VPN diagnostics from verified received state.
6. Add encrypted database export/import and station pairing.
7. Hardware-validate MAVLink, RTSP/OpenIPC, StabX and network behavior when equipment is available.

## Acceptance rule
No decorative telemetry in production UI. Unknown, absent or stale values are unavailable. New protocol backends begin read-only.
