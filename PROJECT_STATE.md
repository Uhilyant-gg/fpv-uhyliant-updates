# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Current priority is the complete OpenIPC camera lifecycle: route-aware discovery, observed hardware identity, guarded normal update, reboot/rediscovery, and verification of the actual post-update identity. UI polish is secondary.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor and firmware remain absent unless observed.

## OpenIPC normal upgrade
For a camera with verified OpenIPC identity, normal update is modeled as the fixed argv `sysupgrade -k -r`. Upgrade readiness requires a valid observed IPv4 address, verified OpenIPC, and observed platform and sensor. Host/user data is never interpolated into the command. Recovery/fullflash remains a separate path.

A guarded `OpenIPCUpgradeAdapter` now exists. It accepts only `upgrade`, revalidates the current device and passes only the observed host plus fixed argv to an injected authenticated transport. Credentials are deliberately outside repository data. The application does not register a transport at startup yet, so destructive execution remains disabled until credentials/transport and the physical SSC30KQ target are validated.

## Reboot and verification
A bounded rediscovery helper now models post-upgrade reboot recovery. It completes only after the target returns with verified OpenIPC evidence. Post-flash verification preserves hardware continuity and accepts the newly observed firmware value for online latest upgrades when no specific expected version was independently known. It never invents the target version.

## Safety invariants
No invented telemetry, hardware identity, stream URLs, firmware version, credentials, pairing state or trust. Firmware, camera presets and video profiles remain separate. Generic ONVIF never implies OpenIPC. Destructive execution remains behind immutable approval/current-identity checks plus an explicit transport adapter.

## Physical boundary
The remaining blocker for real one-click update is authenticated transport validation on the physical camera. Once a credential mechanism is selected/provided, register that transport, run `sysupgrade -k -r`, wait for reboot, rediscover the same host/device, and feed its freshly observed identity into post-flash verification.
