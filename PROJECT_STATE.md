# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. Target controllers: ArduPilot, Betaflight, INAV. Target telemetry protocols: MAVLink, MSP, CRSF. Video and telemetry remain separate runtimes.

## MAVLink phase 1
Code complete in strictly read-only form. Configurable UDP/TCP/serial endpoint, passive identity/telemetry, freshness, diagnostics and smoke coverage exist. Real-FC validation remains hardware-validation-pending.

## Vehicle and telemetry abstraction
A vehicle-level runtime and structured diagnostics foundation exists. Protocol telemetry reaches the vehicle boundary through normalized read-only providers. Missing fields remain null/None and stale values become unavailable rather than being invented.

MAVLink, MSP and CRSF provider adapters now share this boundary. The current application wiring still uses MAVLink by default; selecting and transporting MSP/CRSF is the next integration step.

## MSP
A read-only MSP v1/v2 parsing/runtime foundation exists for Betaflight/INAV. It uses an explicit telemetry-command allowlist, validates checksums, tracks freshness, decodes received identity/attitude/altitude/analog/GPS telemetry and has parser/runtime CI tests. Serial transport/device selection and hardware validation remain pending.

## CRSF
A passive read-only CRSF parsing/runtime foundation exists. It validates CRC, tracks freshness, decodes received battery/GPS/link-quality fields and has parser/runtime CI tests. It never transmits CRSF frames. Transport/device integration and hardware validation remain pending.

## VideoRuntime status
RTSP runtime tracks checking, ready, playing, reconnecting, stalled and error states, connection attempts and last-event time. Bounded UI recovery and manual reconnect/diagnostics exist. Real-camera validation remains pending.

## Camera preset vs video profile
Camera preset is device/firmware configuration. Video profile belongs to a stream. Video profile is not applied as part of camera flashing.

## OpenIPC flashing rule
BAT/fullflash is only for cameras already running a compatible custom OpenIPC setup. Provisioning must identify hardware/flash layout, validate compatibility and images, preserve a recovery path, then verify after flashing.

## Next implementation order
1. Add safe provider selection and real serial transport integration for read-only MSP/CRSF without duplicating UI.
2. Continue RTSP diagnostics and safe first-class OpenIPC device/provisioning work.
3. Add versioned camera presets separately from per-stream video profiles.
4. Add StabX/external-navigation and Starlink/VPN diagnostics from verified received state.
5. Add encrypted database export/import and station pairing.
6. Hardware-validate MAVLink, MSP, CRSF, RTSP/OpenIPC, StabX and network behavior when equipment is available.

## Validation status
CI is configured to compile Python, run normalized-provider plus MSP/CRSF protocol tests, run application/MAVLink self-tests, load QML offscreen, check version consistency and validate signed test metadata when present. Hardware-dependent validation remains explicitly pending.

## Acceptance rule
No decorative telemetry in production UI. Unknown, absent or stale values are unavailable. New protocol backends begin read-only.
