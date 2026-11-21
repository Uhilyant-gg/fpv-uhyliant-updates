# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## UI navigation
The product UI language is Ukrainian. Devices uses a camera-first dark workflow with one primary search action, secondary manual-IP inspection and progressive disclosure of technical identity.

## Route-aware camera discovery
Discovery builds a bounded target plan from active physical private IPv4 subnets, specific OS routes, saved camera addresses and persisted last-seen/manual addresses. Automatic subnet expansion is limited to private /24-or-smaller networks and bounded concurrency/timeouts; default, public, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. Saved, last-seen and manual addresses are checked directly without causing subnet expansion. ICMP is not required.

A candidate enters the result list only after camera evidence is observed. Generic HTTP/ONVIF reachability is not verified OpenIPC. OpenIPC verification uses observed Majestic API or OpenIPC status.cgi evidence. R2D2, hardware identity and stream availability remain separate observations. Platform, SoC, sensor, firmware and Majestic fields are populated only from returned evidence and otherwise remain unavailable. Configured video sections alone do not invent RTSP URLs. The routed regression case 192.168.0.12 -> 192.168.1.50 is covered by an automated planner test.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Provider/router fallback returns unavailable (`None`) rather than synthesizing plausible values. Primary and secondary video runtimes remain isolated. Prepared runtime metadata snapshots fail closed when current metadata changes. Invalid RTSP endpoint metadata remains unavailable instead of being probed or invented.

## Firmware and camera preset safety
Firmware remains guarded with no generic destructive adapter. Camera presets remain separate from video profiles and require post-apply observation.

## Station pairing
Pairing uses durable non-secret metadata plus Windows Credential Manager protected secrets with fail-closed recovery. Peer proof/exchange remains unimplemented without a real protocol contract.

## Remaining platform/hardware boundaries
1. Physically validate route-aware discovery and status.cgi parsing against the SSC30KQ / IMX335 camera.
2. Observe real stream endpoint metadata from the physical OpenIPC/Majestic target before automatically creating streams.
3. Define/obtain a real pairing peer proof/exchange protocol contract.
4. Real StabX / Starlink-WireGuard observations and target-hardware validation.
5. Validate camera firmware/preset execution and dual decoding on physical Windows target hardware.
6. Authenticode when real signing credentials are available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
