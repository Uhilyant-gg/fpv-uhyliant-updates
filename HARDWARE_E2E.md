# OpenIPC physical hardware E2E

This gate prepares the application for destructive physical validation without pretending that CI is hardware evidence.

## Required fresh evidence before execution
- a selected saved device and observed host;
- verified OpenIPC evidence;
- observed platform and sensor;
- an observed safe local discovery route;
- fresh observed device reachability;
- session credentials supplied by the operator;
- an explicitly accepted SSH host key.

Missing or unknown evidence blocks readiness. Generic reachability is not OpenIPC verification.

## Physical validation sequence
Use the normal upgrade path only after the software-side firmware acquisition, compatibility approval and immutable execution plan are ready. The physical session must authenticate, revalidate the bound device identity, dispatch only the fixed normal OpenIPC upgrade command, enter reboot-pending, rediscover, and require fresh matching OpenIPC platform/sensor plus a non-empty observed firmware version before reporting verified.

Recovery/fullflash remains a separate Service Mode workflow and is not part of this normal-upgrade E2E gate.

## Evidence capture
Export a sanitized diagnostic bundle before the physical destructive step and again after post-reboot verification. Record hardware-dependent failures as observed evidence rather than replacing unknown values with assumptions.
