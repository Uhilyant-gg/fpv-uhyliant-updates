# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Baseline and invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Target stacks: ArduPilot, Betaflight, INAV. Target protocols: MAVLink, MSP, CRSF.

Unknown/stale/missing telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Private signing keys and pairing secrets must never be committed or exported in station snapshots.

## Release pipeline
`.github/workflows/automated-ota.yml` is the authoritative unified Windows build/sign/publish path; legacy release and Windows-installer workflows are disabled. A release must build and publish against the workflow event SHA. Do not change release checkout back to a moving branch after build start.

Validate version/channel/prerelease policy before building. Test/development releases must remain prereleases. Carry a SHA-256 digest with the Windows artifact and verify it again after GitHub artifact transport, before manifest signing. Release tags must point to the immutable source SHA; metadata commits are distribution metadata, not the source that produced the binary.

Signing private keys stay in GitHub Secrets and temporary runner storage only. Cleanup must be trap/finally style so a failed command cannot leave the temporary key in later workflow steps. Never commit certificate private keys. Current pipeline signs the OTA release manifest but does not claim Authenticode signing of Windows executables.

## Application security
Portable backups use AES-256-GCM with scrypt and strict allow-listed snapshot validation. Restore is explicit and transactional. Pairing secrets/signing keys are excluded from backup.

## Next work
1. Hardware validation when equipment is available.
2. Station pairing with OS-protected secret storage and explicit trust/revocation.
3. Executable signing when a real code-signing certificate/secret is available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
