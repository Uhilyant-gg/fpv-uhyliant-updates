# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Primary and secondary video runtimes remain isolated while the workspace prevents one stream from driving both decoder roles at once. Primary takeover stops a conflicting secondary selection, PiP shutdown stops only secondary, and late playback events cannot resurrect a stopped runtime.

Prepared video runtimes retain detached canonical source/profile/device metadata snapshots and fail closed when the active device, stream existence/enabled state, stream endpoint metadata, device metadata or referenced video profile changes. Canonical RTSP path normalization is applied consistently at prepare and revalidation time, so equivalent stored paths do not self-invalidate. Device/stream/profile change signals reconcile both decoder roles immediately; invalidated metadata is cleared instead of remaining presented as current, and invalidating secondary disables PiP without stopping a still-valid primary. Reconnect requires the prepared source snapshot to remain current. Invalid RTSP endpoint metadata remains unavailable instead of being probed or invented. Endpoint check timing is reachability timing only, never video latency. Physical Windows dual-decoder validation is still pending.

Read-only link diagnostics preserve unknown measurements; StabX and Starlink/WireGuard still require real observations.

## Firmware and camera preset safety
Firmware remains guarded with no generic destructive adapter. Camera preset execution has a separate guarded lifecycle, rejects video-profile application, and remains hardware-validation-pending without a real adapter. Firmware, camera presets and per-stream video profiles remain separate.

## Station pairing
Pairing uses durable non-secret metadata plus Windows Credential Manager protected secrets with fail-closed recovery. `PairingPanel.qml` remains trust-management only; peer proof/exchange remains unimplemented without a real protocol contract.

## Remaining platform/hardware boundaries
1. Define/obtain a real pairing peer proof/exchange protocol contract before enabling new-pairing UI.
2. Real StabX / Starlink-WireGuard observations and target-hardware validation.
3. Validate camera firmware/preset execution on physical SSC30KQ / IMX335 targets.
4. Validate dual decoding on physical Windows target hardware.
5. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
