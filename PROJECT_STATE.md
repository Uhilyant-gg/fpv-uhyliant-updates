# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Current priority is the complete OpenIPC camera lifecycle plus a reliable packaged Windows update path. UI polish is secondary.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor, variant and firmware remain absent unless observed. Runtime OpenIPC probes use only a validated observed IPv4 plus fixed `/api/v1/config.json` and `/cgi-bin/status.cgi` paths; placeholder URLs are forbidden by regression tests.

## OpenIPC normal upgrade
Normal update is fixed `sysupgrade -k -r` for currently verified compatible OpenIPC only. Credentials are session-only. Authentication precedes destructive execution and current host/OpenIPC/platform/sensor are revalidated immediately before the command. Recovery/fullflash remains separate.

`FirmwareUpdateSession` is the application orchestration boundary around executor, upgrade adapter and reboot verification. It starts without a transport and exposes no credential fields in result/state. `main.py` cannot perform a destructive update without explicit physical transport activation.

## Firmware acquisition
The official upstream catalog is consumed through a fail-closed acquisition boundary. Only complete entries with observed platform + sensor, explicit variant/channel/build, an allowed HTTPS OpenIPC download URL, SHA-256 and bounded positive size become candidates. Variant and build are never guessed. An official selection is bound to catalog generation plus device id, host, verified OpenIPC platform and sensor; any change makes the selection stale before download. Download accepts only that bound catalog selection, not an arbitrary UI artifact map. Cached artifacts are reusable only after exact size and SHA-256 verification; corrupt cache files are discarded. Verified bytes are handed to the existing `FirmwareCenter.verifyImage()` boundary. The manual local-image path remains separate and does not claim official-catalog provenance.

## Reboot and verification
Command dispatch means only `reboot-pending`. Post-reboot rediscovery first retries the destructive dispatch host and may then examine only route-aware bounded private candidates produced by the existing discovery policy. A changed DHCP address is accepted only from fresh OpenIPC endpoint evidence with matching pre-update platform and sensor; an unrelated OpenIPC camera is skipped rather than selected. Success still requires a non-empty actually observed firmware version. Rediscovery remains ICMP-independent and never expands public, default, oversized or known virtual-adapter routes.

## Application updater
The signed test manifest and package SHA-256 remain mandatory. Installation is offered only when `--install-root` resolves to the complete installed launcher layout containing the update helper, launcher and `app/current/FPV-Uhyliant.exe`. Update helper staging, payload self-test, atomic current/rollback switching and startup acknowledgement remain fail-closed.

## Physical boundary
Destructive OpenIPC transport remains disabled at application startup. Real end-to-end camera update still requires actual credentials, accepted SSH host key and explicit destructive hardware validation.
