# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, read-only link diagnostics, AES-GCM backup and transactional restore are implemented software-side.

## Station pairing
Pairing has durable non-secret trust metadata persistence through an atomic, versioned JSON metadata store. Secret bytes never enter that store, portable backup, QML-visible state or repository content.

The Windows Credential Manager adapter implements the protected secret-store boundary with Win32 `CredWriteW`, `CredReadW`, `CredDeleteW` and `CredFree`. Its dedicated Windows CI integration path has passed, covering real Credential Manager write/read/overwrite/delete and registry confirm, restart/reconcile and revoke with durable metadata. Non-Windows systems remain safely unavailable.

Pairing lifecycle recovery is fail-closed. Failed confirm/revoke rollback and missing protected secrets produce explicit recovery state. Reconciliation now returns an explicit success/failure result, never clears recovery state after secret verification or metadata persistence failure, and retries a failed metadata load before assessing trust. New pairing mutations remain blocked until reconciliation actually succeeds.

`PairingPanel.qml` remains protocol-safe: it reports store and recovery state, lists only non-secret trusted metadata, permits explicit revoke when recovery is clean, and exposes a reconciliation retry when recovery is required. It cannot begin or confirm a new pairing session. Peer proof/exchange remains unimplemented because no real protocol contract exists.

## Remaining platform/hardware boundaries
1. Define/obtain a real pairing peer proof/exchange protocol contract before enabling new-pairing UI.
2. Real StabX / Starlink-WireGuard observations and target-hardware validation.
3. Camera firmware/preset execution and dual-decoder validation on physical targets.
4. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
