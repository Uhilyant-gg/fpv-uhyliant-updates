"""Fail-closed contract for applying an accepted Queue v3 repair proposal.

This validates what may be handed to a repository mutation transport. It does not
write files itself. Every requested file must remain on the bound repair branch,
and protected control-plane paths are rejected from autonomous repair.
"""

from __future__ import annotations

from dataclasses import dataclass

from orchestrator_queue_v3_executor_result import RepairResultDecision
from orchestrator_state import PersistedState
from orchestrator_v2 import State, is_protected_path


@dataclass(frozen=True)
class PatchFile:
    path: str
    content: str

    def validate(self) -> None:
        if not self.path.strip() or not self.content.strip():
            raise ValueError("patch-file-incomplete")
        if is_protected_path(self.path):
            raise ValueError("patch-protected-path-blocked")


@dataclass(frozen=True)
class PatchApplicationPlan:
    story_id: str
    baseline_sha: str
    expected_head_sha: str
    files: tuple[PatchFile, ...]
    next_state: State


def build_patch_application_plan(
    *,
    decision: RepairResultDecision,
    persisted: PersistedState,
    files: list[PatchFile],
) -> PatchApplicationPlan:
    persisted.validate()
    if persisted.state != State.REPAIRING:
        raise ValueError("patch-repair-state-required")
    if not decision.ready_for_application or decision.next_state != State.CI_RUNNING:
        raise ValueError("patch-accepted-result-required")
    if decision.accepted.output_type != "patch-proposal":
        raise ValueError("patch-proposal-required")
    if not files:
        raise ValueError("patch-files-required")
    for item in files:
        item.validate()
    paths = [item.path for item in files]
    if len(paths) != len(set(paths)):
        raise ValueError("patch-duplicate-path")
    return PatchApplicationPlan(
        persisted.story_id,
        persisted.baseline_sha,
        persisted.expected_head_sha,
        tuple(files),
        State.CI_RUNNING,
    )
