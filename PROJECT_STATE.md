# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, read-only link diagnostics, AES-GCM backup and transactional restore are implemented software-side.

## Station pairing
Pairing now has durable non-secret trust metadata persistence through an atomic, versioned JSON metadata store. The format is strictly envelope-checked and contains trust metadata only. Pairing secret bytes are never written there and remain excluded from portable station backup.

The trust lifecycle is recovery-aware. Failed metadata persistence after confirmation removes the newly persisted protected secret but keeps the pending in-memory pairing so the user may retry. Reconciliation computes a candidate trust set and only replaces live trust after metadata persistence succeeds, preventing in-memory/disk divergence on metadata write failure.

The application wires the real metadata store under LocalAppData and reconciles it at startup. The secret-store side deliberately remains unavailable, so production pairing cannot begin yet. Enabling pairing still requires a Windows OS-protected secret-store adapter and platform validation. No peer/network proof protocol has been invented.

## OTA/update integrity
OTA remains bound from signed manifest through package SHA-256, strict ready state, guarded ZIP staging and startup acknowledgement/rollback. Release builds remain pinned to immutable source provenance.

## Remaining platform/hardware boundaries
1. Windows OS-protected pairing secret storage plus Windows validation.
2. Pairing peer proof/exchange after a real protocol contract exists.
3. Real StabX / Starlink-WireGuard observers and target-hardware validation.
4. Camera firmware/preset execution and dual-decoder validation on physical targets.
5. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
