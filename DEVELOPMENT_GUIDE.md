# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing persistence
Non-secret trust metadata is persisted at `LocalAppData/FPV-Uhyliant/pairing-trust.json` through `JsonMetadataStore`. The envelope is versioned and exact-field validated; duplicate IDs are rejected. Secret bytes must never enter this file, SQLite, portable backup, QML-visible state or repository content.

`WindowsCredentialSecretStore` stores opaque bytes as Windows generic credentials under the `FPV-Uhyliant/pairing/` target namespace. The real Windows Credential Manager CI path has passed for write/read/overwrite/delete and registry confirm, restart/reconcile and revoke.

## Recovery invariants
Confirmation persists secret then metadata. If metadata persistence fails, secret cleanup must succeed before the registry may accept another pairing mutation. Cleanup failure sets `recoveryError`; never hide it as a normal failure. Reconciliation is the supported retry path.

Revoke first requires the referenced protected secret to exist. It deletes the secret and then persists candidate metadata. If metadata persistence fails, secret restoration is mandatory; restoration failure sets `recoveryError` and blocks further pairing mutation until reconciliation establishes consistency. Never report a missing secret as successful revoke.

## Pairing UI boundary
`PairingPanel.qml` may display store availability, non-secret trusted metadata, errors and reconciliation controls, and may revoke existing trust only while recovery state is clean. It must not expose `secretRef`, secret bytes, `begin`, `confirm`, peer discovery, proof or exchange. Do not enable new pairing until a verified peer protocol contract exists.

## Next work
1. Obtain the real peer pairing protocol contract/evidence before implementing proof/exchange.
2. Continue software-side hardening that does not fabricate peer state.
3. Continue hardware validation and executable signing as equipment/credentials become available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
