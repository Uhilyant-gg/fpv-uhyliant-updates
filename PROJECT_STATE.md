# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. ArduPilot, Betaflight and INAV are target stacks; MAVLink, MSP and CRSF are target telemetry protocols. FPV remains video-first.

## Telemetry
Normalized read-only providers sit behind `TelemetryRouter`; unknown/stale/missing telemetry is unavailable. Real FC/radio validation is `hardware-validation-pending`.

## OpenIPC / firmware
Verified OpenIPC identity stays distinct from generic ONVIF. Firmware Center has SSC30KQ / IMX335 compatibility, primary/upgrade/recovery separation, SHA-256 verification, immutable approvals, pre-handoff re-hash, operation locking and verified post-reboot identity lifecycle. No hardware adapter is registered by default; destructive work is `hardware-validation-pending`.

## Video workspace
`VideoWorkspaceRuntime` owns independent primary and secondary `VideoRuntime` instances. QML has separate Qt `MediaPlayer` and `VideoOutput` paths, with the secondary rendered as a PiP overlay only for two distinct persisted enabled streams. Disabling PiP stops and clears secondary playback; disconnect stops both paths; swapping rebuilds playback from the two real selected stream identities.

Playback health uses observable Qt/runtime events. Endpoint-connect timing remains reachability information, never glass-to-glass latency.

## External navigation / link diagnostics
A read-only `LinkDiagnostics` boundary now models observed external-navigation and network-link state separately. Missing data remains unavailable, observations become stale after their configured freshness window, and network RTT is accepted only when actually supplied by an observer. The FPV diagnostics UI exposes these states without synthesizing StabX, Starlink, VPN, quality or latency values.

Actual StabX protocol ingestion and Starlink/WireGuard OS adapters remain `hardware-validation-pending`; this layer intentionally produces no control output.

## Presets / profiles
Camera presets are versioned hardware-compatible device configuration requiring verified OpenIPC platform/sensor identity. Camera presets remain separate from per-stream video profiles and firmware operations.

## Next implementation order
1. Hardware-only firmware/preset adapters and real SSC30KQ / IMX335 validation remain pending physical hardware.
2. Validate dual-decoder and real RTSP recovery on target Windows hardware (`hardware-validation-pending`).
3. Connect verified read-only StabX/external-navigation and Starlink/VPN observers to the diagnostics boundary when protocol/hardware evidence is available.
4. Add encrypted DB export/import, station pairing and distribution hardening.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation is `hardware-validation-pending`.
