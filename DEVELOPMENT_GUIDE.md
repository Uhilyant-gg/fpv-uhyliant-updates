# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware are separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## OTA trust chain
Treat OTA as one continuous trust chain: signed manifest -> declared package SHA-256 -> downloaded package -> ready state -> updater/helper handoff -> staged payload -> startup acknowledgement/rollback.

`ready.json` is strictly allow-listed and carries version, absolute package path and the digest obtained from the verified signed manifest/download. Always re-hash the package before install handoff. The detached helper receives the expected SHA-256 and must verify the package before extraction and after staging. Do not weaken this to path/version-only trust.

ZIP extraction must validate every member before writing any payload: no traversal outside staging, native/backslash escape ambiguity, symlinks, case-insensitive duplicate destinations, excessive member count or excessive claimed uncompressed size. Only then extract member-by-member.

Pending launcher state records version plus package SHA-256. A startup acknowledgement succeeds only for the fresh random token and expected version. Invalid pending state or failed startup rolls back to the previous application. Package digest is provenance/integrity metadata, not a substitute for the signed manifest.

## Distribution and application security
Release builds remain pinned to the workflow source SHA, artifact hashes are verified across jobs, and OTA manifests use the existing Ed25519 trust path. Portable station backups use AES-256-GCM/scrypt with strict transactional restore. Authenticode remains future work requiring a real certificate/secret.

## Next work
1. Hardware validation when equipment is available.
2. Station pairing with OS-protected secret storage and explicit trust/revocation.
3. Executable signing when real signing credentials are available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
