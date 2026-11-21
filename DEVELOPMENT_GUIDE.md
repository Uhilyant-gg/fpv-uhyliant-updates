# FPV Uhyliant development guide

Read this file, `PROJECT_STATE.md`, `PRODUCT_UX.md`, `DELIVERY_ROADMAP.md` and `AUTONOMOUS_DEVELOPMENT.md` from current `main` before development. `main` is the single source of truth.

## Invariants
Windows ground station: Python + PySide6 + Qt Quick/QML. FPV remains video-first. Unknown telemetry stays unavailable. Cameras, vehicles/flight controllers and operator RC controllers are distinct physical identities composed in the FPV workspace. Camera presets, video profiles and firmware remain separate. Generic ONVIF is not verified OpenIPC. Recovery/fullflash is not a generic install path. Secrets/private signing keys are not repository data. Cloud metadata is not fresh local hardware evidence. AI output is advisory rather than operational authority.

## Product implementation contract
Build around user tasks rather than internal subsystems. Once a usable camera is known, FPV/video is the operational home. The normal path targets `launch -> automatic discover/restore -> verified usable camera -> video -> operate`.

Prefer one contextually useful Next Best Action over exposing a subsystem toolbar. User-facing health uses ready / attention / problem / unknown; detailed subsystem states remain internal or progressively disclosed.

Apply the automation budget to every new prompt or control: if trustworthy observed evidence can determine a value or decision safely and unambiguously, automate it instead of asking the operator. Never automate by guessing unknown identity, telemetry, compatibility or success.

Manual IP and manual controller transport/port configuration are fallbacks to automatic discovery/detection. Advanced contains additional controls for otherwise normal operation. Service Mode contains recovery, manual firmware, fullflash, low-level/developer diagnostics and Hardware E2E validation.

Normal firmware UX exposes the practical device/update decision while catalog, integrity, binding, reboot rediscovery and verification stay internal unless intervention is required. Diagnostics presents the practical problem before technical evidence and offers Fix only for known deterministic non-destructive remediation.

## Account and synchronization boundaries
Account/cloud support is optional for local operation. A cloud device registry may synchronize ownership metadata, added-device records and eligible non-secret preferences across workstations, but locally observed reachability, network coordinates, identity, firmware, streams, telemetry, controller presence and health remain authoritative for the current session.

Sharing and ownership transfer are distinct operations. Sharing is revocable while ownership remains unchanged; transfer deliberately changes ownership. Permissions must be explicit and must not bypass local safety gates.

Do not synchronize session passwords, session credentials, accepted SSH host-key state, destructive approvals or equivalent ephemeral authority as ordinary device metadata.

## Controller boundaries
Prefer automatic local controller detection/restore. Calibration and stick/switch mapping operate on observed inputs. Unknown or unavailable inputs remain unknown. Manual transport configuration belongs in Advanced. Persist/synchronize only non-secret profile/preferences that are safe to restore; never treat a synchronized controller record as proof that the physical controller is currently present or producing valid input.

## AI assistance boundary
AI consumes sanitized structured diagnostic/evidence data only. AI may explain evidence and suggest diagnostic or known-safe remediation paths. AI never becomes authority for identity, telemetry, compatibility, credentials, ownership, firmware success, destructive approval or destructive execution, and it must preserve unknown values.

## Discovery safety
Camera discovery is route-aware but not an Internet scanner. Expand only bounded RFC1918 networks with specific acceptable prefixes; never expand default, public, loopback, multicast, link-local, oversized or virtual-adapter routes. Saved and explicitly entered addresses may be checked directly without implying that their subnet is safe to sweep. Keep concurrency, response size and timeouts bounded. Discovery must not depend on ICMP. Preserve the evidence ladder: reachable service -> camera candidate -> verified OpenIPC -> separately evidenced R2D2 compatibility -> observed hardware identity -> observed streams.

## Authenticated firmware safety
Credentials are session-only. Password fields are masked and cleared on reset/close/shutdown. Passwords must never be logged, persisted, included in snapshots/backups/errors/status/execution plans, shell interpolation or process argv. Password-capable SSH uses a library API with strict known-host verification. Authentication occurs before destructive execution. After authentication, current observed host, verified OpenIPC, platform and sensor must still match the approved compatible device before fixed `sysupgrade -k -r` is allowed.

A completed SSH/sysupgrade invocation is only `reboot-pending`. Success requires bounded rediscovery, fresh verified OpenIPC evidence, fresh platform and sensor, hardware continuity, and a non-empty actually observed post-update firmware version. An unknown authoritative target remains unknown; it must not make a missing observed version pass. Do not infer Ultimate/Lite from hardware or user selection.

## Other lifecycle invariants
Normalized telemetry is tri-state and fallback synthesizes no values. Video runtimes remain isolated and prepared snapshots fail closed after input changes. Pairing secrets and metadata remain separated. Camera presets remain separate from video profiles and require post-apply observation.

## Workflow
Inspect actual `main` and all canonical documents before material product work. `DELIVERY_ROADMAP.md` defines delivery order, dependencies, stories and acceptance criteria. `AUTONOMOUS_DEVELOPMENT.md` defines autonomous work selection, stop conditions, branch/PR behavior, CI repair and the Project Doctor interface.

Work in one substantial, logically complete batch at a time. After each batch, stop for CI evidence. If CI fails, repair that batch before accumulating further product work. Never claim CI or physical hardware success without evidence. Hardware-dependent validation remains explicit.

Autonomous development should proceed without intermediate questions when the answer is derivable from current main, canonical contracts, tests, CI or sanitized evidence. Human intervention is reserved for physical actions, secrets/credentials/keys and genuine product decisions.
