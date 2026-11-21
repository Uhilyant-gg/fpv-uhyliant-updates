# Network diagnostics and remediation

## Goal
Diagnostics must identify practical network and connection failures with minimal operator effort and offer a safe remediation when the fault is deterministic.

## Diagnose first
Read-only checks run before any remediation. The diagnostic result should distinguish at least: local interface unavailable, missing/unsuitable IPv4 configuration, route unavailable, target service unreachable, device reachable but OpenIPC not verified, stream endpoint unavailable, and application-level video failure. Unknown remains unknown.

ICMP is supporting evidence only and is never required for OpenIPC discovery or verification.

## Remediation policy
Network changes are never automatic side effects of diagnosis. The application may propose a fix, but configuration changes run only after an explicit user request.

Every fix must declare what it changes, its target interface/device, whether elevation is required, and how the previous state will be restored when rollback is possible. Re-run the relevant read-only check after the change and report success only from fresh evidence.

## Safe first-line actions
Prefer application-local and non-destructive recovery first: re-run discovery, re-probe the selected device, restart/reconnect the video pipeline, refresh route/interface observations, and retry the verified endpoint.

Operating-system network changes belong behind an explicit repair action and must use a narrow, predefined operation rather than arbitrary shell input. Never accept AI-generated or user-provided free-form commands as a privileged repair action.

## Windows boundary
Windows networking inspection/remediation must live behind a dedicated adapter so diagnostics stays testable without administrator access. Read-only inspection and mutating repair actions are separate APIs. Mutating actions must return structured before/action/after evidence for the diagnostic bundle.

## AI boundary
AI may explain evidence and select from application-defined safe remediation options. It cannot create arbitrary privileged commands or bypass confirmation, validation, rollback, firmware, or flight-control safety boundaries.
