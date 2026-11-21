# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. ArduPilot, Betaflight and INAV are target stacks; MAVLink, MSP and CRSF are target telemetry protocols. FPV remains video-first.

## Telemetry
Normalized read-only providers sit behind `TelemetryRouter`; unknown/stale/missing telemetry is unavailable. Real FC/radio validation is `hardware-validation-pending`.

## OpenIPC / firmware
Verified OpenIPC identity stays distinct from generic ONVIF. Firmware Center remains guarded; no destructive hardware adapter is registered by default.

## Video / diagnostics
Independent primary/secondary video runtimes and real-stream-only PiP are implemented. Playback health is observational. `LinkDiagnostics` keeps external-navigation and network observations separate; real StabX/Starlink/WireGuard adapters remain `hardware-validation-pending`.

## Station backup and restore
Station backup v2 is password-encrypted and authenticated before parsing the station snapshot. The envelope records its schema/version and fixed scrypt parameters; payload confidentiality/integrity use the stdlib authenticated stream construction implemented in `station_backup.py`. Import first authenticates and validates schema plus entity references, then creates an in-memory restore plan. No live data changes until explicit confirmation.

Confirmed restore runs through a single SQLite transaction. Devices, streams, per-stream video profiles, verified OpenIPC identities and active-device selection are replaced atomically; validation failure or SQL/type failure leaves the previous live database state intact. Pairing secrets and signing keys are not part of the snapshot.

## Presets / profiles
Camera presets remain separate from video profiles and firmware operations.

## Next implementation order
1. Hardware-only firmware/preset and real target-device validation remain pending physical hardware.
2. Validate dual-decoder and RTSP recovery on target Windows hardware.
3. Connect verified read-only StabX/external-navigation and Starlink/VPN observers when hardware/protocol evidence is available.
4. Add station pairing and distribution hardening; mature backup cryptography toward a platform/library AEAD when dependency policy permits.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation is `hardware-validation-pending`.
