# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Current priority is the complete OpenIPC camera lifecycle: route-aware discovery, observed hardware identity, guarded normal update, reboot/rediscovery, and verification of the actual post-update identity. UI polish is secondary.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor and firmware remain absent unless observed.

## OpenIPC normal upgrade
For a camera with verified OpenIPC identity, normal update is modeled as the fixed argv `sysupgrade -k -r`. Upgrade readiness requires a valid observed IPv4 address, verified OpenIPC, and observed platform and sensor. Host/user data is never interpolated into the command. Recovery/fullflash remains separate.

A guarded `OpenIPCUpgradeAdapter` revalidates the current device and accepts only `upgrade`. An `ExistingSshTransport` boundary now exists for physical validation using the operating system's already-configured OpenSSH authentication and host trust. It uses batch mode, strict host-key checking and a fixed command; it accepts no password, private key contents, token or host-key bypass from application data.

## Reboot and verification
Bounded rediscovery completes only after verified OpenIPC evidence returns. Post-flash verification preserves hardware continuity and accepts the newly observed firmware value for online latest upgrades when no independently known target version exists. It never invents that version.

## Safety invariants
No invented telemetry, hardware identity, stream URLs, firmware version, credentials, pairing state or trust. Firmware, camera presets and video profiles remain separate. Generic ONVIF never implies OpenIPC. Destructive execution remains behind immutable approval/current-identity checks plus an explicit transport adapter.

## Physical boundary
The application still does not register the destructive SSH transport automatically. Before doing so, the real Windows PC must already be able to authenticate to the target as `root` using OpenSSH non-interactively with trusted host-key verification. That requires the user's external credential/host-trust setup or another explicit credential decision. Once validated, the adapter can be wired to execute the guarded update lifecycle.
