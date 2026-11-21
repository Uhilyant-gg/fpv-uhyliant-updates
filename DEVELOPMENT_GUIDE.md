# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Pairing and links
Pairing secrets and metadata remain separated and fail-closed; peer proof/exchange requires a verified protocol contract. `LinkDiagnostics` accepts real observations only; unknown measurements stay unavailable. Do not infer StabX or Starlink/WireGuard state from names/configuration.

## Firmware execution boundary
Destructive firmware execution requires prepared approval, unchanged artifact SHA-256 and current verified compatible hardware immediately before detached adapter handoff. Post-operation observed verification remains mandatory. No generic destructive adapter is permitted.

## Camera preset execution boundary
Camera presets are device configuration, never firmware and never video profiles. `CameraPresetExecutor` may execute only a prepared plan whose canonical preset ID/version/settings still match a currently verified compatible device. `appliesVideoProfile` must remain false and unknown settings are rejected. Hardware adapters receive a detached camera-only plan. Successful adapter return is not final success: state remains `applied-pending-verification` until a post-apply verified hardware observation is supplied. No real hardware adapter should be registered before physical validation.

## Next work
1. Harden primary/secondary video lifecycle and dual-decoder transitions software-side.
2. Connect real StabX and Starlink/WireGuard observers when observations/contracts are available.
3. Validate firmware/preset executors on physical SSC30KQ / IMX335 targets.
4. Validate dual decoding on physical Windows target hardware.
5. Add Authenticode only when real signing credentials are available.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence.
