# DeepSeek Harness free-machine profile

This profile gives FPV Uhyliant a local-first coding-agent setup on Windows. It does not store API keys in the repository and does not make AI output operational authority.

## Safety contract

- Current `main` and canonical project documents remain authoritative.
- Read `PRODUCT_UX.md`, `PROJECT_STATE.md`, `DEVELOPMENT_GUIDE.md`, `HARDWARE_E2E.md`, `DELIVERY_ROADMAP.md`, and `AUTONOMOUS_DEVELOPMENT.md` before material work.
- AI output is advisory. It cannot establish device identity, compatibility, telemetry, firmware success, destructive approval, or physical Hardware E2E success.
- Never place API keys, passwords, signing keys, device credentials, or raw hardware evidence in prompts, logs, commits, or PR text.
- Work on `automation/<epic>-<purpose>` branches. Never mutate `main` directly.
- Stop for `PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, `PRODUCT_DECISION_REQUIRED`, exhausted repair budget, or unresolved inconsistent evidence.

## Recommended routing

1. `ollama-local`: default for repository inspection, documentation, small patches, and sensitive context.
2. A free cloud provider configured in the Harness Web UI: optional escalation for a bounded task using sanitized context.
3. A second free provider: optional reviewer/fallback.
4. Paid DeepSeek: disabled by default; enable manually only when explicitly intended.

Free-provider model IDs and quotas change. Do not commit provider-specific keys or assume a free endpoint is permanently available.

## Windows bootstrap

Run from the repository root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup_dsh_free_machine.ps1
```

The script validates Node.js, npm, Git, GitHub CLI, Ollama, the selected local model, and the repository safety documents. It prints the next launch command but does not request, store, or modify credentials.

Default model:

```text
qwen3.5:9b-q4_K_M
```

Override it when needed:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup_dsh_free_machine.ps1 -Model "deepseek-r1:8b"
```

## Harness local provider

In Harness open `Settings -> Models -> Add a custom provider` and use:

```text
Provider ID: ollama-local
Base URL: http://<scrubbed-url-domain>/v1
Protocol: openai-compatible
Credential: empty
Model: qwen3.5:9b-q4_K_M
```

Harness-managed credentials belong in its local credential store, never in this repository.

## First bounded task

Ask the agent to read the canonical documents, run `python tools/project_doctor.py`, inspect repository state, and propose one dependency-valid repository-only batch. Require `VERIFIED`, `NOT_VERIFIED`, `BLOCKED_BY_HARDWARE`, and `PROPOSED` labels. Do not authorize push, merge, release, firmware operations, or destructive commands during the first validation cycle.

## Acceptance checks

- The bootstrap exits nonzero when a required executable or canonical document is missing.
- No secret is accepted or persisted.
- The selected Ollama model is verified from `ollama list`.
- The agent starts in the repository root.
- Hardware-dependent claims remain explicitly unverified until supported by physical evidence.
