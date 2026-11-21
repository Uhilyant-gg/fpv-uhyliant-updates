# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing
Non-secret trust metadata and Windows Credential Manager protected secrets are separated. Windows integration coverage has passed. Recovery remains fail-closed. `PairingPanel.qml` may manage existing trust but must not invent peer discovery/proof/exchange without a verified protocol contract.

## Link observation boundary
`LinkDiagnostics` is read-only and must accept only observations supplied by a real observer. Network link state and RTT are independent: a valid state must not require a fabricated RTT. Unknown, malformed, negative, NaN or infinite RTT is represented as `None`, never zero. Invalid observation state must not retain apparently valid measurement fields. Stale data is marked unavailable/stale while retaining the last genuinely observed value for diagnostics; consumers must not treat it as current.

Do not infer StabX state from GPS semantics. Do not infer Starlink/WireGuard link quality, peer state or latency from interface names or configuration. Add concrete adapters only when their output contract comes from real observations/evidence.

## Next work
1. Connect real StabX and Starlink/WireGuard observers when observations/contracts are available.
2. Continue software-side hardening that does not fabricate hardware or peer state.
3. Validate camera firmware/preset execution and dual decoding on physical targets.
4. Add Authenticode only when real signing credentials are available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
