# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows ground station with maximum-video-workspace flight UX. ArduPilot, Betaflight and INAV are target stacks; MAVLink, MSP and CRSF are target telemetry protocols.

## Telemetry
Normalized read-only providers sit behind `TelemetryRouter`; FPV consumes the selected provider and unknown/stale/missing telemetry remains unavailable. Hardware validation is `hardware-validation-pending`.

## OpenIPC and video
Verified OpenIPC identity is distinct from generic ONVIF discovery. Platform/SoC, sensor, firmware and Majestic are populated only from observed verified evidence. Stream diagnostics include main/sub identity plus associated video-profile codec/resolution/FPS/latency-mode metadata and measured endpoint-connect check time. Endpoint timing is reachability data, not glass-to-glass latency. Real camera validation remains `hardware-validation-pending`.

## Firmware Center
SSC30KQ / IMX335 is the initial explicit profile. Primary, upgrade and recovery/fullflash are distinct; recovery/fullflash is only for verified compatible existing custom OpenIPC. SHA-256 verification, immutable approval, immediate pre-handoff re-hash, operation locking and guarded executor lifecycle exist. No hardware adapter is registered by default, so destructive writing remains disabled and reports `hardware-validation-pending`.

The executor now records pre-operation identity and accepts a structured observed post-reboot identity. Post-flash verification checks rediscovery/OpenIPC evidence, platform/sensor compatibility, optional expected firmware and hardware identity continuity before lifecycle state becomes `verified`. Obtaining that observation from real hardware remains `hardware-validation-pending`.

## Presets and profiles
Versioned camera presets remain separate from per-stream video profiles; firmware operations never apply video profiles.

## Next implementation order
1. Implement supported real device adapters only when the actual primary/upgrade/recovery mechanisms are available for hardware validation; do not create generic destructive fallbacks.
2. Continue software-only video work: stream switching state, playback diagnostics, secondary/thermal/PiP preparation.
3. Expand camera presets independently of video profiles.
4. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
5. Add encrypted DB export/import and station pairing; continue distribution hardening.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation is `hardware-validation-pending`.
