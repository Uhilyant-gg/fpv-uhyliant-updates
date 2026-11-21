# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, read-only link diagnostics, AES-GCM backup and transactional restore are implemented software-side.

## OTA/update integrity
OTA remains a signed-manifest trust chain bound through package SHA-256, strict ready state, guarded ZIP staging and startup acknowledgement/rollback. Release builds remain pinned to the immutable workflow SHA and artifact hashes are checked across jobs.

## Station pairing foundation
`PairingRegistry` now separates three states/resources: in-memory pending secrets, OS-protected secret storage, and non-secret persistent trust metadata. Pairing can begin only when both a secret store and metadata store explicitly report availability. Explicit confirmation stores the secret first, then persists trust metadata; if metadata persistence fails, the newly written secret is removed and trust is not granted.

Trusted metadata can be reloaded across process restarts without exposing secret bytes. A reconciliation pass removes trust metadata whose protected secret is no longer present. Revocation deletes the protected secret and then persists removal of trust metadata. Pending secrets remain process-memory-only and are cleared on shutdown.

The default secret and metadata stores remain unavailable, so production pairing is still disabled until real Windows-protected secret storage plus trusted metadata persistence are implemented and validated. Pairing secrets remain excluded from station backup snapshots. No peer/network pairing protocol is invented.

## Hardware/platform boundaries
Windows-protected pairing storage remains `platform-validation-pending`. Real StabX, Starlink/WireGuard observers, target-camera firmware/preset execution and physical dual-decoder validation remain `hardware-validation-pending`. Authenticode requires real signing credentials.

## Next implementation order
1. Implement Windows-protected secret storage and non-secret trust metadata persistence.
2. Add pairing peer proof/exchange only after a real protocol contract exists.
3. Continue hardware validation as equipment becomes available.
4. Add Authenticode when signing credentials are available.

## Acceptance rule
No invented telemetry, hardware identity, stream metadata, latency, pairing peer state or trust. Platform/hardware-dependent validation stays explicit.
