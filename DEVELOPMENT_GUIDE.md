# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing persistence
Non-secret trust metadata is persisted at `LocalAppData/FPV-Uhyliant/pairing-trust.json` through `JsonMetadataStore`. The envelope is versioned and exact-field validated; duplicate IDs are rejected. Secret bytes must never enter this file, SQLite, portable backup, QML-visible state or repository content.

`WindowsCredentialSecretStore` stores opaque bytes as Windows generic credentials under the `FPV-Uhyliant/pairing/` target namespace. It uses the current user's Windows Credential Manager through `ctypes`; no credential is required from the user or repository. On non-Windows platforms it is unavailable by design.

Confirmation persists the protected secret, persists candidate metadata, then publishes live trust. Failed metadata persistence deletes the new secret and leaves pending state retryable. Reconciliation removes metadata only after a successful protected-store absence check and successful metadata write. A protected-store error must remain an error, never fabricated absence.

Revocation reads the protected secret for rollback, deletes it, then persists candidate metadata. If metadata persistence fails, it restores the secret and leaves live trust unchanged. Do not expose the read operation through QML or public pairing state.

## Windows validation
`verify.yml` has a dedicated `windows-pairing-secret-store` job. It runs the pairing unit tests plus a Windows-only integration test against the real Credential Manager API. The integration test uses unique random `pairing/ci-*` keys, cleans them up, checks write/read/overwrite/delete, and verifies registry confirmation, restart/reconciliation and revoke against a temporary metadata store. Do not treat the adapter as platform-validated until this job has completed successfully in CI.

## Pairing enablement boundary
Do not add pairing UI until the Windows Credential Manager CI validation succeeds. Do not implement peer proof/exchange without a verified protocol contract.

## Next work
1. Confirm the Windows pairing-secret-store CI job passes.
2. Only then prepare pairing UI around the validated secret + metadata stores.
3. Add peer proof/exchange only from a verified protocol contract.
4. Continue hardware validation and executable signing as equipment/credentials become available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
