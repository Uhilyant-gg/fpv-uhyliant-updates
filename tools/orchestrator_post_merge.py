"""Deterministic post-merge completion and next-Story handoff."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from orchestrator_state import PersistedState
from orchestrator_v2 import State

HANDOFF_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class MergeEvidence:
    pr: int
    merged: bool
    merged_head_sha: str
    merge_commit_sha: str

    def validate(self) -> None:
        if self.pr <= 0:
            raise ValueError("invalid merged PR")
        if not self.merged:
            raise ValueError("PR is not merged")
        if not self.merged_head_sha:
            raise ValueError("missing merged HEAD SHA")
        if not self.merge_commit_sha:
            raise ValueError("missing merge commit SHA")


@dataclass(frozen=True)
class StoryHandoff:
    schema_version: int
    completed_story_id: str
    completed_pr: int
    completed_head_sha: str
    merge_commit_sha: str
    completed_state: str
    next_story_id: str
    next_baseline_sha: str
    next_state: str
    reason_code: str

    def validate(self) -> None:
        if self.schema_version != HANDOFF_SCHEMA_VERSION:
            raise ValueError("unsupported handoff schema")
        if not self.completed_story_id or self.completed_pr <= 0:
            raise ValueError("invalid completed Story")
        if not self.completed_head_sha or not self.merge_commit_sha:
            raise ValueError("missing completed merge identity")
        if self.completed_state != State.COMPLETE.value:
            raise ValueError("completed state must be COMPLETE")
        if not self.next_story_id:
            raise ValueError("missing next Story")
        if self.next_story_id == self.completed_story_id:
            raise ValueError("next Story must differ")
        if self.next_baseline_sha != self.merge_commit_sha:
            raise ValueError("next baseline must equal merge commit")
        if self.next_state != State.READY.value:
            raise ValueError("next Story must start READY")


def build_handoff(state: PersistedState, evidence: MergeEvidence, next_story_id: str) -> StoryHandoff:
    state.validate()
    evidence.validate()
    next_story_id = next_story_id.strip()
    if state.state != State.UPDATING_STATE:
        raise ValueError("persisted state must be UPDATING_STATE")
    if evidence.pr != state.pr:
        raise ValueError("merged PR does not match persisted binding")
    if evidence.merged_head_sha != state.expected_head_sha:
        raise ValueError("merged HEAD does not match persisted binding")
    if not next_story_id:
        raise ValueError("next Story is required")
    handoff = StoryHandoff(HANDOFF_SCHEMA_VERSION,state.story_id,state.pr,state.expected_head_sha,evidence.merge_commit_sha,State.COMPLETE.value,next_story_id,evidence.merge_commit_sha,State.READY.value,"post-merge-handoff-ready")
    handoff.validate()
    return handoff


def save_handoff(path: Path, handoff: StoryHandoff) -> None:
    handoff.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(asdict(handoff), handle, sort_keys=True, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)
