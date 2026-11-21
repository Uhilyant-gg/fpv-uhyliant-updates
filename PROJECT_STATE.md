# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Product priority
Windows FPV ground station using Python + PySide6 + Qt Quick/QML. Current priority is the complete camera lifecycle: find OpenIPC cameras on reachable local/private routes, verify observed hardware identity, select the correct current OpenIPC update path, perform a guarded update, rediscover, and verify the observed post-update identity. UI polish is secondary for now.

## Discovery
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability is not OpenIPC evidence. Platform, SoC, sensor and firmware remain absent unless observed.

## OpenIPC update path
For a camera with already verified OpenIPC identity, the supported normal update path is OpenIPC `sysupgrade`; the official documentation says newer firmware uses `sysupgrade -k -r` to update kernel and rootfs and that the default source is the GitHub latest release. The application now models this as a fixed argv contract, never shell-interpolated from the camera address. Update readiness requires verified OpenIPC plus observed platform and sensor. Recovery/fullflash stays a separate recovery path and is not the normal upgrade mechanism.

The repository still intentionally has no destructive hardware adapter registered at startup. Actual remote execution requires a credential/transport decision and physical validation on the target camera before it can be enabled. Existing immutable approval, artifact hashing, hardware identity and post-flash verification gates remain in place.

## Safety invariants
No invented telemetry, hardware identity, stream URLs, firmware version, pairing state or trust. Firmware, camera presets and video profiles remain separate. Destructive firmware execution requires a prepared approval and current verified compatible hardware. Generic ONVIF never implies OpenIPC.

## Next implementation block
1. Add authenticated camera transport suitable for the physical OpenIPC target without storing plaintext credentials in repository data.
2. Register a real `sysupgrade -k -r` adapter only after transport validation.
3. Drive the adapter from the discovered/saved camera identity and rediscover the same device after reboot.
4. Compare the post-update observed firmware identity with the new observation rather than inventing an expected version.
