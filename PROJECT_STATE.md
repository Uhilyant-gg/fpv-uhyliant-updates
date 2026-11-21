# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Current priority is the complete OpenIPC camera lifecycle plus a reliable packaged Windows update path. UI polish is secondary.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor, variant and firmware remain absent unless observed. Runtime OpenIPC probes use only a validated observed IPv4 plus fixed `/api/v1/config.json` and `/cgi-bin/status.cgi` paths; placeholder URLs are forbidden by regression tests.

## OpenIPC normal upgrade
Normal update is fixed `sysupgrade -k -r` for currently verified compatible OpenIPC only. Credentials are session-only. The password-capable transport uses a library API and strict known-host verification, while `ExistingSshTransport` remains for OS-configured authentication. Authentication precedes destructive execution and current host/OpenIPC/platform/sensor are revalidated immediately before the command. Recovery/fullflash remains separate.

`FirmwareUpdateSession` is the application orchestration boundary around executor, upgrade adapter and reboot verification. It starts without a transport and exposes no credential fields in result/state. `main.py` cannot perform a destructive update without explicit physical transport activation.

## Application updater
The signed test manifest and package SHA-256 remain mandatory. Installation is offered only when `--install-root` resolves to the complete installed launcher layout containing the update helper, launcher and `app/current/FPV-Uhyliant.exe`. This prevents a partial or direct executable launch from presenting itself as install-ready. Update helper staging, payload self-test, atomic current/rollback switching and startup acknowledgement remain fail-closed.

## Reboot and verification
Command dispatch means only `reboot-pending`. Post-reboot host input is validated before probing. `FirmwareUpdateLifecycle` performs bounded rediscovery, requires fresh verified OpenIPC evidence, and performs profile plus hardware-continuity verification. Success additionally requires a non-empty freshly observed firmware version. An unknown authoritative target version remains unknown and never substitutes for missing observation.

## Physical boundary
Destructive OpenIPC transport remains disabled at application startup. Real end-to-end camera update still requires actual credentials, accepted SSH host key and explicit destructive hardware validation.
