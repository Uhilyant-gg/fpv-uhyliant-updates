# FPV Uhyliant development guide

Read this file and `PROJECT_STATE.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data.

## Discovery safety
Camera discovery is route-aware but not an Internet scanner. Expand only bounded RFC1918 networks with specific acceptable prefixes; never expand default, public, loopback, multicast, link-local, oversized or virtual-adapter routes. Saved and explicitly entered addresses may be checked directly without implying that their subnet is safe to sweep. Keep concurrency, response size and timeouts bounded. Discovery must not depend on ICMP. Preserve the evidence ladder: reachable service -> camera candidate -> verified OpenIPC -> separately evidenced R2D2 compatibility -> observed hardware identity -> observed streams.

## Authenticated firmware safety
Credentials are session-only. Password fields are masked and cleared on reset/close/shutdown. Passwords must never be logged, persisted, included in snapshots/backups/errors/status/execution plans, shell interpolation or process argv. Password-capable SSH uses a library API with strict known-host verification. Authentication occurs before destructive execution. After authentication, current observed host, verified OpenIPC, platform and sensor must still match the approved compatible device before fixed `sysupgrade -k -r` is allowed.

A completed SSH/sysupgrade invocation is only `reboot-pending`. Success requires bounded rediscovery, fresh verified OpenIPC evidence, fresh identity, hardware continuity and the actually observed post-update firmware. Do not invent a latest version. Do not infer Ultimate/Lite from hardware.

## Other lifecycle invariants
Normalized telemetry is tri-state and fallback synthesizes no values. Video runtimes remain isolated and prepared snapshots fail closed after input changes. Pairing secrets and metadata remain separated. Camera presets remain separate from video profiles and require post-apply observation.

## Workflow
Inspect actual `main`, test software/tooling paths, synchronize canonical docs after material changes, and never claim CI success without evidence. Hardware-dependent validation remains explicit.
