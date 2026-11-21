# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. Target controllers: ArduPilot, Betaflight, INAV. Target telemetry protocols: MAVLink, MSP, CRSF. Video and telemetry remain separate runtimes.

## Telemetry architecture
MAVLink, MSP and CRSF use normalized read-only providers behind `TelemetryRouter`. FPV OSD and the main telemetry panel consume the selected normalized provider rather than hard-coding MAVLink telemetry. Unknown fields remain unavailable. Provider selection is persistent; invalid saved selections fall back to MAVLink. Real FC/radio validation remains hardware-validation-pending.

## OpenIPC / video
Verified OpenIPC identity persists separately from generic device data. Generic ONVIF/name hints do not establish OpenIPC. Platform/SoC, sensor, firmware and Majestic values are retained only when observed. Stream-aware RTSP diagnostics distinguish main/sub streams. Real SSC30KQ / IMX335 and camera validation remain hardware-validation-pending.

## Firmware Center
Firmware workflow is Detect -> Identify -> Select firmware -> Pre-check -> Flash -> Reboot -> Rediscover -> Verify. SSC30KQ / IMX335 is the first explicit compatibility profile. Primary installation, upgrade and recovery/fullflash are distinct policies. Recovery/fullflash requires verified compatible existing custom OpenIPC. Firmware images require SHA-256 verification. Successful pre-check produces an immutable approval bound to device/profile/mode/image/hardware identity. A non-destructive execution plan re-validates that approval before any future executor is allowed. Hardware executors are not attached yet; destructive writes are not performed.

## Presets and profiles
Versioned camera-presets now have an explicit device/hardware compatibility boundary. Camera presets remain separate from per-stream video profiles. Firmware operations do not apply video profiles.

## Persistence and startup
SQLite persists devices, streams, video profiles, verified OpenIPC identity and active device. QML startup failures emit diagnostics and transports shut down normally.

## Updater integrity
Signed manifest and package SHA-256 verification are required. Immediately before install, updater binds `ready.json` to the verified manifest and re-hashes the package.

## Next implementation order
1. Hardware-validation-pending must not block software-only work.
2. Add executor interfaces for primary/upgrade/recovery without enabling unsafe generic flashing; re-hash immediately before executor handoff and preserve operation locks/verification contract.
3. Continue OpenIPC video stream metadata, codec/resolution/FPS diagnostics and switching.
4. Expand versioned camera presets independently of video profiles.
5. Add StabX/external-navigation and Starlink/VPN diagnostics from verified received state.
6. Add encrypted DB export/import and station pairing; continue distribution hardening.

## Acceptance rule
No decorative telemetry or invented hardware state. Unknown/stale/missing is unavailable. New telemetry/control backends start read-only. Hardware-dependent validation is `hardware-validation-pending`.
