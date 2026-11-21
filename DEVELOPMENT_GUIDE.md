# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing
Non-secret trust metadata and Windows Credential Manager protected secrets are separated. Windows integration coverage has passed. Recovery remains fail-closed. `PairingPanel.qml` may manage existing trust but must not invent peer discovery/proof/exchange without a verified protocol contract.

## Link observation boundary
`LinkDiagnostics` is read-only and must accept only real observations. Network state must not require fabricated RTT. Unknown/invalid numeric values remain `None`. Do not infer StabX or Starlink/WireGuard state from names or configuration.

## Firmware execution boundary
Destructive execution requires a prepared plan, matching immutable approval, unchanged artifact SHA-256, an existing device and a still-verified OpenIPC identity matching the approved platform/sensor immediately before handoff. Treat device identity as mutable observation: approval never permanently proves later hardware state. Pass detached artifact and plan snapshots to hardware adapters so mutable center state cannot alter an in-flight handoff. Post-operation observed verification remains mandatory. Do not create a generic destructive adapter; real camera execution stays hardware-validation-pending.

Camera presets remain separate device configuration. They never belong to firmware and never apply a video profile.

## Next work
1. Connect real StabX and Starlink/WireGuard observers when observations/contracts are available.
2. Validate firmware/preset executors on physical SSC30KQ / IMX335 targets before enabling destructive paths.
3. Validate dual decoding on physical Windows target hardware.
4. Add Authenticode only when real signing credentials are available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
