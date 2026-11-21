# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. Target controllers: ArduPilot, Betaflight, INAV. Target telemetry protocols: MAVLink, MSP, CRSF. Video and telemetry remain separate runtimes.

## Telemetry architecture
MAVLink, MSP and CRSF use normalized read-only providers behind `TelemetryRouter`. FPV OSD and the main telemetry panel now consume the selected normalized provider rather than hard-coding MAVLink telemetry. Unknown fields remain unavailable.

MAVLink remains the default. MSP has a serial transport that polls only the explicit read-only MSP command allowlist. CRSF serial transport is passive and does not transmit. COM/baud/enabled configuration is persistent. Real FC/radio validation remains hardware-validation-pending.

## Vehicle and diagnostics
A vehicle-level runtime and structured diagnostics foundation exists above the selected telemetry provider and video runtime. Protocol switching does not require duplicate vehicle UI.

## VideoRuntime status
RTSP runtime tracks checking, ready, playing, reconnecting, stalled and error states, connection attempts and last-event time. Bounded UI recovery and manual reconnect/diagnostics exist. Real-camera validation remains pending.

## Persistence and startup
SQLite persists devices, streams, video profiles and the active device. QML startup failures emit Qt diagnostics to CI and stop telemetry transports cleanly. Smoke tests use normal Qt shutdown.

## Updater integrity
Signed manifest and package SHA-256 verification are required. Immediately before install, the updater binds `ready.json` to the currently verified manifest and re-hashes the downloaded package. CI auto-discovers all application `test_*.py` tests.

## Camera preset vs video profile
Camera preset is device/firmware configuration. Video profile belongs to a stream. Video profile is not applied as part of camera flashing.

## OpenIPC flashing rule
BAT/fullflash is only for cameras already running a compatible custom OpenIPC setup. Provisioning must identify hardware/flash layout, validate compatibility and images, preserve a recovery path, then verify after flashing.

## Next implementation order
1. Hardware-validation-pending for MAVLink/MSP/CRSF must not block software work.
2. Continue RTSP diagnostics and make OpenIPC camera a first-class verified device.
3. Implement Firmware Center: Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify, beginning with SSC30KQ / IMX335 while keeping primary/upgrade/recovery-fullflash paths separate.
4. Add versioned camera presets separately from per-stream video profiles.
5. Add StabX/external-navigation and Starlink/VPN diagnostics from verified received state.
6. Add encrypted database export/import and station pairing.

## Validation status
Normal CI compiles Python, runs all application tests, exercises application/MAVLink self-tests and loads QML offscreen. The Windows release pipeline now also runs all application unit tests before freezing and explicitly includes Qt SerialPort in the PyInstaller build. Hardware-dependent validation remains explicitly pending.

## Acceptance rule
No decorative telemetry in production UI. Unknown, absent or stale values are unavailable. New protocol backends begin read-only.
