# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, read-only link diagnostics, AES-GCM backup and transactional restore are implemented software-side.

## OTA/update integrity
OTA remains a signed-manifest trust chain bound through package SHA-256, strict ready state, guarded ZIP staging and startup acknowledgement/rollback. Release builds remain pinned to the immutable workflow SHA and artifact hashes are checked across jobs.

## Station pairing foundation
A software-side pairing trust lifecycle now exists with pending, explicit confirmation, trusted and revoked/cancelled paths. Pairing secrets are generated locally and never exposed through the public QML-facing records. Trust is not granted unless an injected secret store reports that it is available and successfully persists the secret.

The default secret-store implementation is deliberately unavailable. Therefore production pairing is currently disabled until a real OS-protected Windows secret-store adapter is implemented and validated. Pairing secrets are not part of station backup snapshots. Pending secrets live only in process memory and are cleared on application shutdown.

## Hardware/platform boundaries
A Windows OS-protected secret-store adapter is `platform-validation-pending`. Real StabX, Starlink/WireGuard observers, target-camera firmware/preset execution and physical dual-decoder validation remain `hardware-validation-pending`. Authenticode still requires a real signing certificate/secret.

## Next implementation order
1. Implement and validate Windows-protected pairing secret storage without repository-stored secrets.
2. Add pairing identity/proof transport only after its real protocol is defined; do not invent a peer protocol.
3. Continue hardware validation as target equipment becomes available.
4. Add Authenticode when real signing credentials are available.

## Acceptance rule
No invented telemetry, hardware identity, stream metadata, latency, pairing peer state or trust. Hardware/platform-dependent validation stays explicit.
