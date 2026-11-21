# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. ArduPilot, Betaflight and INAV are target stacks; MAVLink, MSP and CRSF are target telemetry protocols. FPV remains video-first.

## Telemetry
Normalized read-only providers sit behind `TelemetryRouter`; unknown/stale/missing telemetry is unavailable. Real FC/radio validation is `hardware-validation-pending`.

## OpenIPC / firmware
Verified OpenIPC identity stays distinct from generic ONVIF. Firmware Center has SSC30KQ / IMX335 compatibility, primary/upgrade/recovery separation, SHA-256 verification, immutable approvals, pre-handoff re-hash, operation locking and verified post-reboot identity lifecycle. No hardware adapter is registered by default; destructive work is `hardware-validation-pending`.

## Video workspace
`VideoWorkspaceRuntime` owns independent primary and secondary `VideoRuntime` instances. QML has separate Qt `MediaPlayer` and `VideoOutput` paths, with the secondary rendered as a PiP overlay only for two distinct persisted enabled streams. Disabling PiP stops and clears secondary playback; disconnect stops both paths; swapping rebuilds playback from the two real selected stream identities. Primary and secondary recovery counters, errors, attempts, last observable events and configured metadata remain isolated.

Playback health uses observable Qt/runtime playing, stopped, error, reconnect and stall events. Stream diagnostics expose associated profile codec/resolution/FPS/latency-mode only when configured and endpoint-connect timing only as reachability information, never invented glass-to-glass latency. Qt-unavailable dropped-frame or measured-latency values are not synthesized.

## Presets / profiles
Versioned camera presets remain separate from per-stream video profiles. Firmware operations never apply video profiles.

## Next implementation order
1. Hardware-only firmware adapters and real SSC30KQ / IMX335 validation remain pending physical hardware.
2. Validate dual-decoder performance and real RTSP recovery on target Windows hardware (`hardware-validation-pending`).
3. Expand camera presets separately from stream video profiles.
4. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
5. Add encrypted DB export/import, station pairing and distribution hardening.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation is `hardware-validation-pending`.
