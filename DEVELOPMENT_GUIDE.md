# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Video lifecycle
Primary and secondary `VideoRuntime` instances are isolated. A single stream must not be prepared in both decoder roles simultaneously. Primary selection wins conflicts by stopping secondary first; secondary preparation rejects the current primary stream. Disabling PiP stops secondary only. Reconnect must revalidate that the selected stream still exists and is enabled. Invalid/missing RTSP host, port or path is unavailable and must not trigger a probe. Late player callbacks after stop must not resurrect runtime state. Endpoint check time is reachability timing only, never video latency.

Physical dual-decoder capability and performance remain Windows hardware-validation-pending.

## Pairing and links
Pairing secrets and metadata remain separated and fail-closed; peer proof/exchange requires a verified protocol contract. `LinkDiagnostics` accepts real observations only. Do not infer StabX or Starlink/WireGuard state from names/configuration.

## Firmware and preset execution
Destructive firmware execution requires prepared approval, unchanged SHA-256 and current verified compatible hardware. Camera presets are separate device configuration, reject video-profile mutation, and require post-apply observation. No generic destructive hardware adapter is permitted before physical validation.

## Next work
1. Run physical Windows dual-decoder/RTSP validation when target hardware is available.
2. Connect real StabX and Starlink/WireGuard observers when observations/contracts are available.
3. Validate firmware/preset executors on physical SSC30KQ / IMX335 targets.
4. Add Authenticode only when real signing credentials are available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
