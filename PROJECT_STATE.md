# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. ArduPilot, Betaflight and INAV are target stacks; MAVLink, MSP and CRSF are target telemetry protocols. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Firmware remains guarded with no destructive hardware adapter enabled by default. Independent primary/secondary video runtimes, real-stream-only PiP, camera presets, link diagnostics, and AES-GCM station backup/transactional restore are implemented software-side. Hardware-dependent validation remains pending where documented.

## Distribution hardening
The unified release pipeline now builds from the immutable workflow-trigger SHA instead of re-reading a moving `main`. Release input policy is validated in shared tooling, and non-stable channels must remain prereleases. Windows build artifacts carry a SHA-256 sidecar that is verified again after artifact download before release signing/publishing. Artifact names include the source SHA and retention is bounded.

Release publishing keeps signing material in the GitHub secret boundary, writes the temporary private key only under the runner temp directory, and removes it through an EXIT trap. The release tag is explicitly anchored to the immutable source SHA rather than the later metadata commit. Legacy release/installer workflows remain disabled entry points; the unified pipeline is authoritative.

CI now runs tooling unit tests in addition to application tests and rejects common private-key/certificate artifact extensions. This hardening does not claim Windows Authenticode signing; executable code-signing remains a separate future capability requiring an appropriate certificate/secret.

## External/hardware boundaries
Real StabX, Starlink/WireGuard observers, target-camera firmware/preset execution and real dual-decoder validation remain `hardware-validation-pending`.

## Next implementation order
1. Hardware validation when target devices become available.
2. Station pairing with OS-protected secrets and explicit trust/revocation lifecycle.
3. Add executable signing/provenance hardening when the required certificate/secret is available.

## Acceptance rule
No invented telemetry, hardware state, stream metadata or latency. Hardware-dependent validation stays explicit.
