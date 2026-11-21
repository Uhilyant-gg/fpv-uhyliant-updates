# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. ArduPilot, Betaflight and INAV are target stacks; MAVLink, MSP and CRSF are target telemetry protocols. FPV remains video-first.

## Telemetry / OpenIPC / video
Normalized read-only telemetry providers preserve unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no destructive hardware adapter enabled by default. Independent primary/secondary video runtimes and real-stream-only PiP are implemented; hardware validation remains pending where documented.

## Station backup and restore
Station backup v3 now uses the repository's existing `cryptography` dependency: scrypt derives an AES-256 key and AES-GCM provides authenticated encryption. Envelope schema/version, KDF/cipher identifiers, KDF parameters, salt and nonce are authenticated as associated data. Wrong passwords or modified ciphertext/metadata are rejected before a snapshot can become pending restore state.

Portable snapshots are strictly allow-listed and type/range/reference validated before restore. They contain devices, streams, per-stream video profiles, verified OpenIPC identities and active-device selection only. Pairing secrets and signing keys are excluded.

Restore stays two-phase and explicit. Inspection never changes live SQLite state; confirmed restore performs the replacement in one transaction, so validation or write failures preserve the prior database.

## External navigation / link diagnostics
`LinkDiagnostics` remains a read-only observation boundary. Real StabX and Starlink/WireGuard adapters remain `hardware-validation-pending`.

## Next implementation order
1. Hardware-only firmware/preset and real target-device validation when physical hardware is available.
2. Validate dual-decoder and RTSP recovery on target Windows hardware.
3. Connect verified read-only external-navigation/network observers when protocol evidence is available.
4. Add station pairing with OS-protected secrets and explicit trust/revocation lifecycle, then continue distribution hardening.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation is `hardware-validation-pending`.
