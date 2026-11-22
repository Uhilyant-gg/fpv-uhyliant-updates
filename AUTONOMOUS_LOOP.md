# FPV Uhyliant autonomous loop closure

Status: implementation batch active.

Baseline: `aa5fa25af87e459bb42ea4cbe2b7d9fcad794361`.

## Goal
Close the software-development lifecycle so routine work can progress without repeated human prompts:

`project state -> autonomous Story selection -> reviewable PR -> CI/evidence -> guarded merge -> post-merge handoff -> next autonomous run`

## Existing boundary
The autonomous developer creates reviewable changes through safe outputs. The privileged merge workflow is separately guarded and currently manually dispatched. The implementation must connect these stages without weakening deterministic authorization.

## Required invariants
- Current `main` and canonical documents are authoritative.
- E0 physical OpenIPC Hardware E2E remains deferred and incomplete until real physical evidence exists.
- CI or simulation never becomes physical evidence.
- Protected changes retain their security/review requirements.
- Merge authorization remains bound to exact PR, baseline and expected HEAD evidence.
- Autonomous progress stops only for `PHYSICAL_ACTION_REQUIRED`, `SECRET_REQUIRED`, or `PRODUCT_DECISION_REQUIRED`, or a fail-closed software/security error requiring repair.
- No autonomous workflow performs destructive physical firmware execution.

## Completion contract
This batch is complete only when repository workflows provide a deterministic handoff from an eligible autonomous PR through guarded merge to the next autonomous software run, while preserving all existing safety boundaries and avoiding unbounded or duplicate runs.
