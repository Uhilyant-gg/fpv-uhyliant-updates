# OpenIPC physical hardware E2E

This gate prepares the application for destructive physical validation without pretending that CI is hardware evidence.

## Required fresh evidence before execution
- a selected saved device and observed host;
- verified OpenIPC evidence;
- observed platform and sensor;
- an observed safe local discovery route;
- fresh observed device reachability;
- verified firmware artifact and immutable normal-upgrade execution plan bound to that device;
- session credentials supplied by the operator;
- an explicitly accepted SSH host key bound to the approved transaction.

Missing or unknown evidence blocks readiness. Generic reachability is not OpenIPC verification.

## Validated Windows test artifact
Physical validation uses the manually dispatched `FPV Uhyliant Hardware E2E Build` workflow. It checks out the exact workflow source SHA, runs source tests, builds a Windows Hardware E2E executable, validates packaged QML plus backend/GUI smoke tests, and uploads a non-publishing artifact named `hardware-e2e-<source SHA>`.

The artifact contains the Windows application archive, `package.sha256`, and `hardware-e2e-build.json`. The provenance file records the exact source SHA, application version, package name and SHA-256 and marks the build purpose as physical OpenIPC Hardware E2E. This workflow does not publish OTA/release metadata and does not require release-signing secrets.

Before physical testing, use an artifact produced from the exact green source SHA intended for validation. Preserve `hardware-e2e-build.json` with the staged diagnostic evidence so the tested binary remains attributable to source.

## Physical validation sequence
Use the normal upgrade path only after software-side firmware acquisition, compatibility approval and immutable execution plan are ready. The physical session must authenticate against the approved device, revalidate the bound device identity and approval, dispatch only the fixed normal OpenIPC upgrade command, enter reboot-pending, rediscover, and require fresh matching OpenIPC platform/sensor plus a non-empty observed firmware version before reporting verified.

Recovery/fullflash remains a separate Service Mode workflow and is not part of this normal-upgrade E2E gate.

## Evidence capture
Export a sanitized diagnostic bundle before the physical destructive step. After the terminal outcome, save `post-update` evidence on success or `failure` evidence on failure. Keep those staged captures together with `hardware-e2e-build.json`. Record hardware-dependent failures as observed evidence rather than replacing unknown values with assumptions.
