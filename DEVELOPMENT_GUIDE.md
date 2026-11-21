# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Discovery safety
Camera discovery is route-aware but not an Internet scanner. Expand only bounded RFC1918 networks with specific acceptable prefixes; never expand default, public, loopback, multicast, link-local, oversized or virtual-adapter routes. Saved and explicitly entered addresses may be checked directly without implying that their subnet is safe to sweep. Keep concurrency, response size and timeouts bounded. Discovery must not depend on ICMP.

Preserve the evidence ladder: reachable service -> camera candidate -> verified OpenIPC -> separately evidenced R2D2 compatibility -> observed hardware identity -> observed streams. A generic ONVIF response, hostname hint or open TCP port must never become verified OpenIPC. Do not create a device for an address that supplied no camera/service evidence. OpenIPC identity fields must contain only values actually returned by Majestic/OpenIPC endpoints; absent values stay absent.

## UI language and workflow
All user-facing UI copy is Ukrainian when a natural Ukrainian equivalent exists. Preserve product/protocol identifiers. Devices should lead with `Знайти камери`; manual IP is a secondary escape hatch that runs the same fingerprint pipeline. Network routes, metrics, fingerprints and raw evidence belong in progressive disclosure, not the primary workflow. Keep the visual language compact, dark, high-contrast and video-first.

## Telemetry lifecycle
Normalized telemetry is tri-state where the protocol observation can be absent. Provider/router fallback must expose every normalized field as unavailable (`None`), not synthesize plausible values. Stale measurement values are removed.

## Video lifecycle
Primary and secondary `VideoRuntime` instances are isolated. A single stream must not be prepared in both decoder roles simultaneously. Prepared runtime metadata snapshots fail closed when device, stream or profile data changes. Endpoint check time is reachability timing only, never video latency.

## Pairing, links, firmware and presets
Pairing secrets and metadata remain separated and fail-closed; peer proof/exchange requires a verified protocol contract. `LinkDiagnostics` accepts real observations only. Destructive firmware execution requires prepared approval, unchanged SHA-256 and current verified compatible hardware. Camera presets remain separate from video profiles and require post-apply observation.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence. Hardware-dependent validation remains explicit.
