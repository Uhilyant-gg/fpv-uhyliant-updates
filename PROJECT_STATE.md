# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Current priority is the complete OpenIPC camera lifecycle: route-aware discovery, observed hardware identity, guarded authenticated normal update, reboot/rediscovery, and verification of the actual post-update identity. UI polish is secondary.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor, variant and firmware remain absent unless observed.

## OpenIPC normal upgrade
For a camera with verified OpenIPC identity, normal update is the fixed `sysupgrade -k -r`. `CameraCredentials` holds username/password in memory only and exposes only non-secret snapshot state. `AuthenticatedCameraTransport` uses password authentication without putting the password in process argv; SSH host keys are fail-closed against the system known-hosts set. Authentication must succeed before destructive execution, then device host/platform/sensor/OpenIPC evidence is revalidated immediately before the fixed command.

`ExistingSshTransport` remains available for OS-configured SSH authentication. Recovery/fullflash remains separate. No transport is registered automatically in `main.py`, so software completion does not silently enable destructive hardware execution.

## Reboot and verification
Successful command dispatch means `reboot-pending`, never update success. Bounded rediscovery completes only after fresh verified OpenIPC evidence returns. Post-flash verification requires hardware continuity and reports the newly observed firmware value when no independently authoritative target version exists. Ultimate/Lite is not guessed.

## Safety invariants
No invented telemetry, hardware identity, variant, stream URLs, firmware version, credentials, pairing state or trust. Firmware, camera presets and video profiles remain separate. Generic ONVIF never implies OpenIPC. Destructive execution remains behind immutable approval/current-identity checks plus an explicit transport adapter. Secrets never enter execution plans or persistent repository/application metadata.

## Physical boundary
The next step requires real-camera authentication/host-key validation and explicit destructive hardware validation. Real credentials are not repository data and must not be invented.
