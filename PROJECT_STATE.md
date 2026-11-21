# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Current priority is the complete OpenIPC camera lifecycle: route-aware discovery, observed hardware identity, guarded authenticated normal update, reboot/rediscovery, and verification of the actual post-update identity. UI polish is secondary.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor, variant and firmware remain absent unless observed.

## OpenIPC normal upgrade
Normal update is fixed `sysupgrade -k -r` for currently verified compatible OpenIPC only. Credentials are session-only. The password-capable transport uses a library API and strict known-host verification, while `ExistingSshTransport` remains for OS-configured authentication. Authentication precedes destructive execution and current host/OpenIPC/platform/sensor are revalidated immediately before the command. Recovery/fullflash remains separate.

`FirmwareUpdateSession` is the application orchestration boundary around executor, upgrade adapter and reboot verification. It starts without a transport, does not retain the configured transport itself, and exposes no credential fields in result/state. `main.py` cannot perform a destructive update without explicit physical transport activation.

## Reboot and verification
Command dispatch means only `reboot-pending`. Post-reboot host input is validated before probing. `FirmwareUpdateLifecycle` performs bounded rediscovery, requires fresh verified OpenIPC evidence, and performs profile plus hardware-continuity verification. Success additionally requires a non-empty freshly observed firmware version. An unknown authoritative target version remains unknown and never substitutes for missing observation. Generic reachability cannot complete the lifecycle.

## Safety audit
The pre-hardware audit covers authentication failure, command immutability, identity changes, rediscovery timeout/generic-host rejection, missing OpenIPC evidence, changed hardware, missing observed firmware, secret boundaries, disabled-by-default destructive wiring, and separation of normal upgrade from recovery/fullflash. Ultimate/Lite is not inferred or hardcoded into detection/update verification.

## Physical boundary
Software orchestration and pre-hardware safety checks are complete. Destructive transport remains disabled at application startup. Further real end-to-end validation requires the physical camera's actual credentials, accepted SSH host key and explicit destructive hardware run; these are not invented.
