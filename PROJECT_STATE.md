# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, read-only link diagnostics, AES-GCM backup and transactional restore are implemented software-side.

## Station pairing
Pairing has durable non-secret trust metadata persistence through an atomic, versioned JSON metadata store. Secret bytes never enter that store, portable backup, QML-visible state or repository content.

The Windows Credential Manager adapter implements the protected secret-store boundary with Win32 `CredWriteW`, `CredReadW`, `CredDeleteW` and `CredFree`. Its dedicated Windows CI integration path has now passed, covering real Credential Manager write/read/overwrite/delete and registry confirm, restart/reconcile and revoke with durable metadata. Non-Windows systems remain safely unavailable.

Pairing confirmation remains commit-after-persist and retryable. Reconciliation never converts a secret-store read failure into a fabricated missing-secret state. Revocation reads the protected secret, deletes it, persists candidate metadata, and restores the secret if metadata persistence fails. Duplicate metadata record IDs are rejected.

A protocol-safe `PairingPanel.qml` trust-management foundation now reports secret/metadata store readiness, lists only non-secret trusted metadata and permits explicit revoke behind confirmation. It deliberately cannot begin or confirm a new pairing session, and explicitly states that peer proof/exchange is not implemented. It is not yet exposed as a production pairing entry point because no real peer protocol contract exists.

## Remaining platform/hardware boundaries
1. Define/obtain a real pairing peer proof/exchange protocol contract before enabling new-pairing UI.
2. Real StabX / Starlink-WireGuard observations and target-hardware validation.
3. Camera firmware/preset execution and dual-decoder validation on physical targets.
4. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
