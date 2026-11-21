# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no generic destructive adapter. Independent primary/secondary video, real-stream-only PiP, camera presets, read-only link diagnostics, AES-GCM backup and transactional restore are implemented software-side.

## OTA/update integrity
The signed manifest still authenticates release metadata and package SHA-256. Download now persists the verified digest into an exact-field ready state. Installation re-hashes the package before handing it to the detached update helper, passes the expected digest explicitly, and the helper verifies it again before extraction and again after staging. This closes the previous gap where helper extraction trusted only a path/version argument.

ZIP staging now rejects traversal paths, backslash member names, case-insensitive duplicate destinations, symbolic links, excessive member counts and excessive declared uncompressed size. Extraction is performed member-by-member only after the package digest and member set pass validation.

Launcher pending-startup state is bound to the package digest. Pending state without a valid version/digest is not accepted as a successful update candidate. Startup acknowledgement remains token + version bound; on success the digest is recorded as `lastGoodPackageSha256`, while failed pending startup uses rollback.

## Distribution hardening
The authoritative release pipeline builds from an immutable workflow SHA, carries/verifies artifact SHA-256 across jobs, constrains release channel policy, and keeps signing private material in the runner secret/temp boundary. Authenticode remains future work requiring a real code-signing certificate/secret.

## Hardware boundaries
Real StabX, Starlink/WireGuard observers, target-camera firmware/preset execution and physical dual-decoder validation remain `hardware-validation-pending`.

## Next implementation order
1. Hardware validation when target devices become available.
2. Station pairing with OS-protected secrets and explicit trust/revocation lifecycle.
3. Authenticode/executable signing when the required certificate/secret becomes available.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation stays explicit.
