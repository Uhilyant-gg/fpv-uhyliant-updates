# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing trust boundary
Pairing uses separate secret and metadata boundaries. Pending secret bytes exist only in process memory. Persistent trusted metadata may contain ID, label, endpoint, fingerprint, timestamps, state and an opaque secret reference, but never secret bytes.

Pairing requires both stores to be available. Confirmation must be explicit. Persist the protected secret before trust metadata; if metadata persistence fails, remove the newly written secret and do not create trust. Revocation deletes the protected secret before persisting removal of trust metadata. On startup/reconnect, a reconciliation pass may discard metadata whose protected secret is missing.

Do not put pairing secrets into SQLite, JSON metadata, station backup, environment variables, repository files or QML-visible properties. Do not implement peer proof/exchange until a real protocol contract is available. Default stores remain intentionally unavailable until platform implementations exist.

## OTA/application security
OTA stays bound from signed manifest through package digest, guarded extraction and startup rollback. Portable backups use AES-256-GCM/scrypt with strict transactional restore. Release builds stay pinned to immutable source provenance.

## Next work
1. Add Windows-protected secret-store adapter plus non-secret metadata persistence.
2. Validate that platform implementation on Windows before enabling pairing UI.
3. Add peer proof/exchange only from a real protocol contract.
4. Continue hardware validation and executable signing when equipment/credentials exist.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
