# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. Target controllers: ArduPilot, Betaflight, INAV. Target telemetry protocols: MAVLink, MSP, CRSF. Video and telemetry remain separate runtimes.

## MAVLink phase 1
Code complete in strictly read-only form. Configurable UDP/TCP/serial endpoint, passive identity/telemetry, freshness, diagnostics and smoke coverage exist. Real-FC validation remains hardware-validation-pending.

## Vehicle and telemetry abstraction
A vehicle-level runtime and structured diagnostics foundation exists. MAVLink, MSP and CRSF now have normalized providers behind a stable read-only `TelemetryRouter`, so provider selection can change without replacing the vehicle/UI contract. Missing fields remain null/None and stale values become unavailable rather than being invented.

The application instantiates all three provider runtimes and exposes the router to QML. MAVLink remains the default active provider. MSP/CRSF serial transport/device selection is still pending, so the router does not fabricate connectivity for those providers.

## MSP and CRSF
Read-only MSP v1/v2 and passive CRSF parsing/runtime foundations exist with freshness/checksum/CRC tests. MSP/CRSF serial transport/device selection and hardware validation remain pending.

## VideoRuntime status
RTSP runtime tracks checking, ready, playing, reconnecting, stalled and error states, connection attempts and last-event time. Bounded UI recovery and manual reconnect/diagnostics exist. Real-camera validation remains pending.

## Persistence and startup
SQLite persists devices, streams, video profiles and the active device. CI includes a regression test that reloads the database and verifies active-device persistence/removal. QML startup failures emit Qt diagnostics to CI and shut down MAVLink cleanly; smoke tests use normal Qt shutdown.

## Updater integrity
Signed manifest and package SHA-256 verification remain required. Immediately before install, the updater binds `ready.json` to the currently verified manifest and re-hashes the downloaded package so a changed/stale package is rejected. CI auto-discovers all `test_*.py` unit tests.

## Camera preset vs video profile
Camera preset is device/firmware configuration. Video profile belongs to a stream. Video profile is not applied as part of camera flashing.

## OpenIPC flashing rule
BAT/fullflash is only for cameras already running a compatible custom OpenIPC setup. Provisioning must identify hardware/flash layout, validate compatibility and images, preserve a recovery path, then verify after flashing.

## Next implementation order
1. Add serial transport/device handling for read-only MSP/CRSF and expose safe provider selection in UI.
2. Continue RTSP diagnostics and safe first-class OpenIPC device/provisioning work.
3. Add versioned camera presets separately from per-stream video profiles.
4. Add StabX/external-navigation and Starlink/VPN diagnostics from verified received state.
5. Add encrypted database export/import and station pairing.
6. Hardware-validate MAVLink, MSP, CRSF, RTSP/OpenIPC, StabX and network behavior when equipment is available.

## Validation status
CI compiles Python, automatically runs all application `test_*.py` unit tests, runs application/MAVLink self-tests, loads QML offscreen, checks version consistency and validates signed test metadata when present. Hardware-dependent validation remains explicitly pending. The most recent CI result must still be confirmed independently before it is called successful.

## Acceptance rule
No decorative telemetry in production UI. Unknown, absent or stale values are unavailable. New protocol backends begin read-only.
