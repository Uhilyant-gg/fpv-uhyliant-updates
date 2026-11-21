# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Product/UI baseline
Windows ground station: Python + PySide6 + Qt Quick/QML. Home -> Devices / Quick connect / Firmware / Update / Diagnostics -> FPV or Service Mode. FPV remains video-first.

## Non-negotiable rules
- ArduPilot, Betaflight, INAV; MAVLink, MSP, CRSF.
- New telemetry/control backends begin read-only. Unknown/stale/missing state is unavailable.
- Camera presets and video profiles are separate; video profiles belong to streams and are not applied by firmware flashing.
- Generic ONVIF/name hints do not establish OpenIPC.
- Primary, upgrade and recovery/fullflash are distinct. Recovery/fullflash is only for verified compatible existing custom OpenIPC.
- Destructive writes require observed hardware/layout compatibility, verified image, recovery path, immutable approval, pre-handoff re-hash, operation lock, reboot/rediscovery and post-operation verification.

## Current architecture
Telemetry provider integration and serial MSP/CRSF foundations exist; hardware validation remains pending.

OpenIPC verified identity persistence exists. Video diagnostics are stream-aware and may expose codec/resolution/FPS/latency-mode only from the stream's configured video profile. Endpoint connection timing may be reported as a network/reachability diagnostic but must not be labelled as glass-to-glass video latency.

Firmware Center has SSC30KQ / IMX335 compatibility, SHA-256 verification, immutable approval and guarded executor lifecycle. Hardware executor adapters remain disabled by default. Pure post-flash validation verifies observed rediscovery identity, OpenIPC evidence, platform/sensor, optional expected firmware and identity continuity. Real post-reboot acquisition is `hardware-validation-pending`.

Versioned camera presets are independent of per-stream video profiles.

## Next work
1. Connect post-reboot observed identity from future supported adapters to executor verification.
2. Continue main/sub switching and playback diagnostics; prepare secondary/thermal/PiP without synthesizing metadata.
3. Expand camera presets without coupling them to stream profiles.
4. Add verified StabX/external-navigation and Starlink/VPN diagnostics.
5. Add encrypted DB export/import, station pairing and distribution hardening.

## Workflow
Inspect actual `main`, test software paths, mark hardware-only checks `hardware-validation-pending`, keep canonical docs synchronized after material changes, and never claim CI/write success without evidence.
