# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. Target controllers: ArduPilot, Betaflight, INAV. Target telemetry protocols: MAVLink, MSP, CRSF. Video and telemetry remain separate runtimes.

## Telemetry architecture
MAVLink, MSP and CRSF use normalized read-only providers behind `TelemetryRouter`. FPV OSD consumes the selected provider; unknown fields remain unavailable. Real FC/radio validation is `hardware-validation-pending`.

## OpenIPC / video
Verified OpenIPC identity persists separately from generic device data. Generic ONVIF/name hints do not establish OpenIPC. Platform/SoC, sensor, firmware and Majestic values are retained only when observed. Stream-aware RTSP diagnostics distinguish main/sub streams. Real camera validation is `hardware-validation-pending`.

## Firmware Center
Workflow: Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify. SSC30KQ / IMX335 is the initial compatibility profile. Primary, upgrade and recovery/fullflash are distinct. Recovery/fullflash requires verified compatible existing custom OpenIPC. Firmware image SHA-256 is verified and immutable approval binds device/profile/mode/image/hardware identity.

A guarded `FirmwareExecutor` boundary now exists. It re-hashes the artifact immediately before executor handoff, enforces a single-device operation lock, and requires post-operation rediscovery/identity verification. No hardware adapter is registered by default, so destructive execution remains disabled and reports `hardware-validation-pending`.

## Presets and profiles
Versioned camera presets are separate from per-stream video profiles. Firmware operations do not apply video profiles.

## Next implementation order
1. Implement real adapter contracts for supported primary/upgrade/recovery paths only after their hardware-specific mechanisms are known and testable; no generic fullflash.
2. Add rediscovery/firmware-version verification implementation around the executor state machine.
3. Improve OpenIPC stream metadata and diagnostics: codec/resolution/FPS/latency, switching, secondary/thermal/PiP preparation.
4. Expand versioned camera presets independently of video profiles.
5. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
6. Add encrypted DB export/import and station pairing; continue distribution hardening.

## Acceptance rule
No decorative telemetry or invented hardware state. Unknown/stale/missing is unavailable. New telemetry/control backends start read-only. Hardware-dependent validation is `hardware-validation-pending`.
