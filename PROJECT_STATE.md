# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Independent primary/secondary video, real-stream-only PiP, camera presets, AES-GCM backup and transactional restore are implemented software-side.

Read-only link diagnostics preserve unknown measurements and reject invalid numeric observations. StabX and Starlink/WireGuard still require real observers/evidence before their state can be populated.

## Firmware safety
Firmware remains guarded with no generic destructive adapter. The executor now revalidates immutable approval, execution-plan identity, artifact SHA-256, device existence and current verified OpenIPC platform/sensor immediately before adapter handoff. The adapter receives detached artifact/plan snapshots rather than live mutable center objects. Post-operation verification remains required. Camera preset execution remains separate from firmware and video profiles.

## Station pairing
Pairing has durable non-secret trust metadata persistence and Windows Credential Manager protected secrets. Windows CI integration has passed. Pairing recovery is fail-closed. `PairingPanel.qml` remains trust-management only; peer proof/exchange remains unimplemented because no real protocol contract exists.

## Remaining platform/hardware boundaries
1. Define/obtain a real pairing peer proof/exchange protocol contract before enabling new-pairing UI.
2. Real StabX / Starlink-WireGuard observations and target-hardware validation.
3. Camera firmware/preset execution and dual-decoder validation on physical targets.
4. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
