# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product direction
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Target stacks: ArduPilot, Betaflight and INAV; target telemetry protocols: MAVLink, MSP and CRSF. FPV remains video-first.

## Runtime architecture
Normalized telemetry preserves unknown/stale state. Verified OpenIPC identity stays distinct from generic ONVIF. Independent primary/secondary video, real-stream-only PiP, camera presets, AES-GCM backup and transactional restore are implemented software-side. Read-only link diagnostics preserve unknown measurements; StabX and Starlink/WireGuard still require real observations.

## Firmware and camera preset safety
Firmware remains guarded with no generic destructive adapter. The executor revalidates approval, artifact digest and current verified hardware identity immediately before its detached adapter handoff. Post-operation verification remains required.

Camera preset execution now has a separate guarded executor lifecycle. It accepts only a prepared preset plan that still matches a verified compatible device and a canonical preset/version, rejects video-profile application and unknown settings, passes a detached plan to a hardware adapter, and requires an explicit post-apply verified hardware observation. No real preset hardware adapter is registered, so actual execution remains hardware-validation-pending. Camera presets remain separate from firmware and per-stream video profiles.

## Station pairing
Pairing has durable non-secret trust metadata persistence and Windows Credential Manager protected secrets. Windows CI integration has passed. Pairing recovery is fail-closed. `PairingPanel.qml` remains trust-management only; peer proof/exchange remains unimplemented because no real protocol contract exists.

## Remaining platform/hardware boundaries
1. Define/obtain a real pairing peer proof/exchange protocol contract before enabling new-pairing UI.
2. Real StabX / Starlink-WireGuard observations and target-hardware validation.
3. Validate camera firmware/preset execution and dual decoding on physical targets.
4. Authenticode when signing credentials become available.

## Acceptance rule
No invented telemetry, hardware identity, pairing peer state, trust, stream metadata or latency. Platform/hardware-dependent validation stays explicit.
