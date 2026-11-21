# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, AES-GCM backup and transactional restore are implemented software-side.

Read-only link diagnostics now harden the observation boundary itself: network state can be observed without an RTT measurement; malformed, negative, NaN or infinite RTT remains unknown instead of becoming zero or crashing the observer; invalid states discard untrusted measurement fields; stale observations remain explicitly stale while preserving the last actually observed value. StabX and Starlink/WireGuard still require real observers/evidence before their state can be populated.

## Station pairing
Pairing has durable non-secret trust metadata persistence through an atomic, versioned JSON metadata store and Windows Credential Manager protected secrets. The dedicated Windows CI integration path has passed. Pairing lifecycle recovery is fail-closed, and reconciliation has explicit success/failure semantics. `PairingPanel.qml` remains trust-management only; peer proof/exchange remains unimplemented because no real protocol contract exists.

## Remaining platform/hardware boundaries
1. Define/obtain a real pairing peer proof/exchange protocol contract before enabling new-pairing UI.
2. Real StabX / Starlink-WireGuard observations and target-hardware validation.
3. Camera firmware/preset execution and dual-decoder validation on physical targets.
4. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
