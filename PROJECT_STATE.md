# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, read-only link diagnostics, AES-GCM backup and transactional restore are implemented software-side.

## Station pairing
Pairing has durable non-secret trust metadata persistence through an atomic, versioned JSON metadata store. Secret bytes never enter that store, portable backup, QML-visible state or repository content.

A Windows Credential Manager adapter implements the protected secret-store boundary with Win32 `CredWriteW`, `CredReadW`, `CredDeleteW` and `CredFree`. Credentials use an application-scoped target for the current Windows user. Non-Windows systems remain safely unavailable.

Pairing confirmation remains commit-after-persist and retryable. Reconciliation never converts a secret-store read failure into a fabricated missing-secret state. Revocation reads the protected secret, deletes it, persists candidate metadata, and restores the secret if metadata persistence fails. Duplicate metadata record IDs are rejected.

On Windows, `PairingRegistry` selects the protected adapter and combines it with the LocalAppData metadata store already supplied by the application. A Windows CI job now exercises the real Credential Manager API, including write/read/overwrite/delete plus `PairingRegistry` confirm, restart/reconcile and revoke with durable metadata. This validation remains pending until that CI job completes successfully. Pairing UI and peer/network proof exchange remain pending; no peer protocol has been invented.

## Remaining platform/hardware boundaries
1. Obtain successful Windows Credential Manager CI validation before enabling production pairing UI.
2. Pairing peer proof/exchange after a real protocol contract exists.
3. Real StabX / Starlink-WireGuard observations and target-hardware validation.
4. Camera firmware/preset execution and dual-decoder validation on physical targets.
5. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
