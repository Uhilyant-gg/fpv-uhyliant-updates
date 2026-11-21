# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing trust boundary
`PairingRegistry` owns software trust lifecycle metadata only. `begin()` may create an in-memory pending secret only when a secret-store adapter explicitly reports availability. Public pending/trusted records expose a SHA-256 fingerprint and metadata, never the secret bytes.

`confirm()` requires explicit approval and must persist the secret successfully before creating a trusted record. `revoke()` must delete the protected secret before removing trust metadata. `cancel()` and shutdown clear pending in-memory secrets. Portable station backup must remain pairing-secret-free.

Do not implement pairing transport by assumption. There is currently no verified peer proof/exchange protocol in the repository, so network pairing remains pending a real protocol decision/evidence. The default secret store is intentionally unavailable; do not replace it with plaintext files, SQLite secrets, environment variables or repository material.

## OTA/application security
OTA remains bound from signed manifest through package digest, guarded extraction and startup rollback. Portable backups use AES-256-GCM/scrypt with strict transactional restore. Release builds remain pinned to immutable source provenance.

## Next work
1. Add an OS-protected Windows secret-store adapter and validate it on Windows.
2. Add peer proof/exchange only from a real protocol contract.
3. Continue hardware-dependent validation and executable signing when required equipment/secrets exist.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
