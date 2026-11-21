# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing persistence
Non-secret pairing trust metadata is persisted at `LocalAppData/FPV-Uhyliant/pairing-trust.json` through `JsonMetadataStore`. The envelope is versioned and exact-field validated before records are accepted. Secret bytes must never enter this file, SQLite, portable backup, QML-visible state or repository content.

Pairing confirmation is recovery-safe: persist protected secret, persist candidate metadata, then publish live trust. If metadata persistence fails, delete the new secret and leave the in-memory pending item available for retry. Reconciliation is also commit-after-persist so a metadata write failure cannot silently desynchronize live trust from disk.

The default secret store remains unavailable. Therefore the presence of the metadata store alone must never enable pairing. A Windows OS-protected secret adapter must be implemented and validated before pairing UI is enabled. Peer proof/exchange still requires a real protocol contract.

## Other trust boundaries
OTA stays bound from signed manifest through package SHA-256, guarded extraction and startup rollback. Portable backups use AES-256-GCM/scrypt and explicit transactional restore. Release builds remain pinned to immutable source provenance.

## Next work
1. Implement Windows-protected pairing secret storage and validate it on Windows.
2. Add pairing UI only after both stores are operational.
3. Add peer proof/exchange only from a verified protocol contract.
4. Continue hardware validation and executable signing as equipment/credentials become available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
