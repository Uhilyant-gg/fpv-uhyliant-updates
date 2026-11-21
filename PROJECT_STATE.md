# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Current priority is the complete OpenIPC camera lifecycle: route-aware discovery, observed hardware identity, guarded authenticated normal update, reboot/rediscovery, and verification of the actual post-update identity. UI polish is secondary.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor, variant and firmware remain absent unless observed.

## OpenIPC normal upgrade
For a camera with verified OpenIPC identity, normal update is the fixed `sysupgrade -k -r`. `CameraCredentials` holds username/password in memory only. `AuthenticatedCameraTransport` keeps passwords out of process argv and uses strict known-host verification. Authentication precedes destructive execution, followed by current host/OpenIPC/platform/sensor revalidation. `ExistingSshTransport` remains available for OS-configured authentication. Recovery/fullflash remains separate. No destructive transport is automatically registered in `main.py`.

## Reboot and verification
Successful command dispatch means only `reboot-pending`. `FirmwareUpdateLifecycle` is now the sole software path from reboot-pending to verified: it runs bounded `FirmwareRediscovery`, requires fresh verified OpenIPC evidence, then performs post-flash profile and hardware-continuity verification. A generic reachable host cannot complete the lifecycle. When no independently authoritative target version exists, the firmware result is the freshly observed value rather than an invented expected latest version.

## Safety invariants
No invented telemetry, hardware identity, variant, stream URLs, firmware version, credentials, pairing state or trust. Firmware, camera presets and video profiles remain separate. Generic ONVIF never implies OpenIPC. Destructive execution remains behind immutable approval/current-identity checks plus an explicit transport adapter. Secrets never enter execution plans or persistent repository/application metadata. Ultimate/Lite is not inferred from platform or sensor.

## Physical boundary
Software orchestration now stops before physical enablement. Real-camera authentication/known-host validation and an explicit destructive run on the test camera require real credentials and hardware validation; they are not enabled automatically or invented.
