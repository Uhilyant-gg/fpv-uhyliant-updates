# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## UI navigation
The product UI language is Ukrainian. User-facing controls should not mix English UI labels when a clear Ukrainian equivalent exists; protocol/product identifiers such as FPV, RTSP, OpenIPC, MAVLink, MSP, CRSF, StabX, Starlink and WireGuard remain identifiers. The application has an explicit Home surface with entry points for Devices, Quick Connect, Firmware, Update and Diagnostics. Devices now uses a camera-first dark workflow with one primary search action, secondary manual-IP inspection and progressive disclosure of technical identity.

## Route-aware camera discovery
Discovery builds a bounded target plan from active physical private IPv4 subnets, specific OS routes and saved/manual camera addresses. Automatic subnet expansion is limited to private /24-or-smaller networks and bounded concurrency/timeouts; default, public, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. Saved/manual addresses are direct candidates rather than reasons to expand a subnet. ICMP is not required.

A candidate enters the result list only after a camera/service endpoint responds. Generic ONVIF or a reachable host is not verified OpenIPC. OpenIPC verification uses observed Majestic API or OpenIPC status.cgi evidence. R2D2, hardware identity and stream availability remain separate observations. Platform, SoC, sensor, firmware and Majestic fields are populated only from returned evidence and otherwise remain unavailable. The routed regression case 192.168.0.12 -> 192.168.1.50 is covered by an automated planner test.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Provider/router fallback returns the full normalized field set as unavailable (`None`) rather than synthesizing `connected=false` or a health value. MSP and CRSF follow the same boundary before the first valid frame.

Primary and secondary video runtimes remain isolated while the workspace prevents one stream from driving both decoder roles at once. Prepared video runtimes retain detached canonical source/profile/device metadata snapshots and fail closed when current metadata changes. Invalid RTSP endpoint metadata remains unavailable instead of being probed or invented. Endpoint check timing is reachability timing only, never video latency.

## Firmware and camera preset safety
Firmware remains guarded with no generic destructive adapter. Camera preset execution has a separate guarded lifecycle, rejects video-profile application, and remains hardware-validation-pending without a real adapter. Firmware, camera presets and per-stream video profiles remain separate.

## Station pairing
Pairing uses durable non-secret metadata plus Windows Credential Manager protected secrets with fail-closed recovery. Peer proof/exchange remains unimplemented without a real protocol contract.

## Remaining platform/hardware boundaries
1. Physically validate route-aware discovery and status.cgi parsing against the SSC30KQ / IMX335 camera.
2. Define/obtain a real pairing peer proof/exchange protocol contract.
3. Real StabX / Starlink-WireGuard observations and target-hardware validation.
4. Validate camera firmware/preset execution on physical targets.
5. Validate dual decoding on physical Windows target hardware.
6. Authenticode when real signing credentials are available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
