# FPV Uhyliant project state

`main` is the single source of truth. Historical chat code must not replace newer repository code.

## Current priority
The software foundation for the guarded OpenIPC update path is now mature enough that the next milestone is integrated validation rather than more isolated defensive hardening. The immediate goal is to make the complete camera journey observable, deterministic and ready for real-hardware E2E:

`discover -> verify OpenIPC -> observe hardware identity -> select compatible official firmware -> verify artifact -> authenticate -> explicit guarded update -> reboot -> bounded rediscovery -> observe post-update identity/firmware`.

UI work should support this journey and expose only decisions the user actually needs to make. Internal mechanisms remain available only where they are required for diagnostics or an explicit advanced/manual path.

## Discovery and device identity
Discovery is route-aware and bounded. Saved, last-seen and manual IPv4 addresses are direct candidates. Public/default, loopback, multicast, link-local, oversized and known virtual-adapter routes are not swept. ICMP is not required. Generic reachability or ONVIF is not OpenIPC evidence.

Protected endpoints may surface an authentication-required candidate, but authentication alone never upgrades it to verified OpenIPC. Platform, SoC, sensor, variant and firmware remain unknown unless observed. The evidence ladder remains:

`reachable service -> camera candidate -> verified OpenIPC -> separately evidenced R2D2 compatibility -> observed hardware identity -> observed streams`.

The camera selected in Firmware Center is also the device bound to hardware preflight. Changing that selected device invalidates host-key acceptance. A missing/unknown explicit device selection fails closed rather than silently falling back to another camera.

## Automatic Firmware Center
The normal user path uses the selected/active verified OpenIPC camera and derives a supported firmware profile only from observed platform + sensor. A profile is never guessed from a UI choice. If no unique supported profile exists, automatic update remains blocked.

The official OpenIPC catalog is consumed through a fail-closed acquisition boundary. Only complete entries with observed platform + sensor, explicit variant/channel/build, an allowed HTTPS OpenIPC download URL, SHA-256 and bounded positive size become candidates. Variant/build ambiguity requires an explicit advanced choice. The catalog selection is bound to catalog generation plus device id, host, verified OpenIPC platform and sensor. Any change makes it stale.

Downloaded or cached artifacts must pass exact size and SHA-256 verification before entering the existing Firmware Center artifact boundary. Manual local firmware remains a separate expert path and must not be presented as the recommended automatic flow.

For normal `upgrade`, recovery-path and flash-layout confirmations are not prerequisites. Those gates remain applicable to the separate primary/recovery/fullflash paths where required. Recovery/fullflash is never a universal OpenIPC update method.

## Destructive update safety
Normal OpenIPC update remains fixed `sysupgrade -k -r` for currently verified compatible OpenIPC only. Credentials are session-only. Password fields are masked and cleared on reset/close/shutdown, and passwords must not enter logs, persistence, diagnostics, status, execution plans, shell interpolation or process argv.

Authentication and accepted SSH host-key state precede destructive execution. Immediately before execution, the approved device, current host, verified OpenIPC state, observed platform/sensor, approval, execution plan and firmware artifact integrity must still match. Any stale or changed input fails closed.

The destructive operation remains an explicit user action. A successful command dispatch means only `reboot-pending`, never successful update.

## Reboot and post-update verification
Post-reboot verification uses the host bound at destructive dispatch and bounded route-aware rediscovery. A changed DHCP address may be accepted only from fresh OpenIPC evidence with matching pre-update platform and sensor. Unrelated OpenIPC devices are skipped.

Update success requires fresh verified OpenIPC evidence, hardware continuity and a non-empty actually observed post-update firmware version. Missing authoritative firmware remains unknown and cannot be interpreted as success.

## Diagnostics and observability
Diagnostics is now part of the hardware-validation path, not a separate future feature. The local diagnostics boundary should remain deterministic and sanitized, preserving unknown values rather than inventing health data. Diagnostic export is the evidence capture mechanism for physical E2E failures.

Continue improving lifecycle observability where real-hardware debugging needs it: correlate camera/device identity, firmware acquisition state, preflight/auth state, executor phase, rediscovery result and bounded errors/warnings. Secrets, credentials and private signing material must never be exported.

AI-assisted diagnosis, if added later, consumes the same sanitized evidence and never becomes an authority for destructive actions.

## Application updater
The packaged Windows updater remains a parallel release-readiness track. Signed manifest validation and package SHA-256 remain mandatory. Installation is offered only for a complete installed launcher layout. Helper staging, payload self-test, atomic current/rollback switching and startup acknowledgement remain fail-closed.

Do not let application-updater polish block the next OpenIPC hardware E2E unless a packaging defect prevents producing/running the test build.

## Next execution order
1. Complete the remaining cross-boundary audit of the automatic Firmware Center journey, especially invalidation between camera selection, catalog selection, preflight/auth, execution plan and executor handoff.
2. Add only the diagnostics/structured lifecycle evidence needed to make a real-camera failure reproducible and diagnosable.
3. Produce a testable build and run real OpenIPC hardware E2E with actual session credentials and explicit SSH host-key acceptance.
4. Fix failures from real hardware evidence immediately and repeat the E2E until the guarded lifecycle completes or a genuine hardware/external blocker is identified.
5. Validate the complete user journey including discovery, manual-IP fallback, identity/add/active-camera state, automatic firmware selection, authentication, guarded update, reboot, rediscovery and observed firmware.
6. Perform the larger video-first UI/UX and release-readiness pass after the integrated hardware journey is stable.

## Hardware E2E success contract
Software-only CI does not prove physical update success. A hardware E2E pass requires observed evidence for the same logical camera across the lifecycle:

- verified OpenIPC before update;
- observed platform + sensor before update;
- compatible verified firmware artifact;
- ready preflight bound to the selected camera;
- authenticated guarded destructive execution;
- reboot-pending after dispatch;
- bounded rediscovery after reboot;
- fresh verified OpenIPC identity with matching hardware continuity;
- non-empty observed post-update firmware.

If any item is missing, report the stage and evidence instead of claiming update success.

## Stable product invariants
FPV remains video-first. Camera presets, video profiles and firmware are separate entities. Firmware update must not apply a video profile. Unknown telemetry/state remains unknown. Recovery/fullflash is separate from normal update. Destructive firmware transport stays disabled at startup and requires the normal explicit safety/approval path.
