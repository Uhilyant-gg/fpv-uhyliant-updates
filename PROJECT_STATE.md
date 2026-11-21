# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. ArduPilot, Betaflight and INAV are target stacks; MAVLink, MSP and CRSF are target telemetry protocols. FPV remains video-first.

## Telemetry
Normalized read-only providers sit behind `TelemetryRouter`; unknown/stale/missing telemetry is unavailable. Real FC/radio validation is `hardware-validation-pending`.

## OpenIPC / firmware
Verified OpenIPC identity stays distinct from generic ONVIF. Firmware Center has SSC30KQ / IMX335 compatibility, primary/upgrade/recovery separation, SHA-256 verification, immutable approvals, pre-handoff re-hash, operation locking and verified post-reboot identity lifecycle. No hardware adapter is registered by default; destructive work is `hardware-validation-pending`.

## Video workspace
`VideoWorkspaceRuntime` owns independent primary and secondary `VideoRuntime` instances. QML has separate Qt playback/render paths and real-stream-only PiP. Playback health uses observable Qt/runtime events; endpoint timing is reachability only.

## External navigation / link diagnostics
`LinkDiagnostics` models observed external-navigation and network-link state separately. Missing data remains unavailable and observations age to stale. Real StabX and Starlink/WireGuard adapters remain `hardware-validation-pending`.

## Station backup foundation
A versioned station snapshot now covers devices, streams, video profiles, verified OpenIPC identities and active-device selection. Export writes a portable manifest with SHA-256 integrity. Import is inspection/planning only: schema, digest and entity references are validated, but live SQLite state is not changed without a future explicit restore decision. Backup encryption and actual restore execution are not yet implemented.

## Presets / profiles
Camera presets are versioned hardware-compatible device configuration requiring verified OpenIPC platform/sensor identity. Camera presets remain separate from per-stream video profiles and firmware operations.

## Next implementation order
1. Hardware-only firmware/preset adapters and real SSC30KQ / IMX335 validation remain pending physical hardware.
2. Validate dual-decoder and real RTSP recovery on target Windows hardware (`hardware-validation-pending`).
3. Connect verified read-only StabX/external-navigation and Starlink/VPN observers when evidence is available.
4. Add encrypted backup envelope, explicit transactional restore, station pairing and distribution hardening.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation is `hardware-validation-pending`.
