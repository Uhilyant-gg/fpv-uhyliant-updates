# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing persistence
Non-secret trust metadata is persisted at `LocalAppData/FPV-Uhyliant/pairing-trust.json` through `JsonMetadataStore`. The envelope is versioned and exact-field validated; duplicate IDs are rejected. Secret bytes must never enter this file, SQLite, portable backup, QML-visible state or repository content.

`WindowsCredentialSecretStore` stores opaque bytes as Windows generic credentials under the `FPV-Uhyliant/pairing/` target namespace. It uses the current user's Windows Credential Manager through `ctypes`; no credential is required from the user or repository. On non-Windows platforms it is unavailable by design.

Confirmation persists the protected secret, persists candidate metadata, then publishes live trust. Failed metadata persistence deletes the new secret and leaves pending state retryable. Reconciliation removes metadata only after a successful protected-store absence check and successful metadata write. A protected-store error must remain an error, never fabricated absence. Revocation reads the protected secret for rollback and restores it if metadata persistence fails.

## Windows validation
The dedicated `windows-pairing-secret-store` CI path has passed against the real Windows Credential Manager API. Coverage includes write/read/overwrite/delete and registry confirmation, restart/reconciliation and revoke with durable metadata.

## Pairing UI boundary
`PairingPanel.qml` is limited to trust-store status, non-secret trusted metadata and explicit revoke. Policy tests prohibit `begin`, `confirm` and `secretRef` from that UI. It is intentionally not yet wired as a production new-pairing entry point. Do not add peer discovery, proof, exchange or new-pairing actions until a verified protocol contract exists.

## Next work
1. Obtain the real peer pairing protocol contract/evidence before implementing proof/exchange.
2. Continue software-side work that does not fabricate peer state while pairing protocol is unavailable.
3. Continue hardware validation and executable signing as equipment/credentials become available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
