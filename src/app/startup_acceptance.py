"""Deterministic repository-software contract for the first-run journey."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from first_run_acceptance import evaluate_first_run


THRESHOLD_MS = 10_000
UI_STAGES = (
    "launch",
    "restore",
    "discovery",
    "window-visible",
    "health",
    "devices",
    "next-action",
)


def _events(events: Iterable[Mapping[str, object]] | None) -> tuple[Mapping[str, object], ...]:
    if not isinstance(events, (list, tuple)):
        return ()
    return tuple(event for event in events if isinstance(event, Mapping))


def startup_acceptance_report(
    events: Iterable[Mapping[str, object]] | None,
    *,
    threshold_ms: int = THRESHOLD_MS,
) -> dict:
    rows = _events(events)
    by_stage: dict[str, Mapping[str, object]] = {}
    for event in rows:
        stage = event.get("stage")
        if isinstance(stage, str) and stage not in by_stage:
            by_stage[stage] = event

    stages = []
    for stage in UI_STAGES:
        event = by_stage.get(stage)
        elapsed = event.get("elapsedMs") if event else None
        stages.append({
            "stage": stage,
            "present": event is not None,
            "status": event.get("status") if event else "missing",
            "elapsedMs": elapsed if isinstance(elapsed, int) else None,
        })

    missing = [stage["stage"] for stage in stages if not stage["present"]]
    failed_stage = missing[0] if missing else None
    reason = "startup-stages-incomplete" if failed_stage else None
    failed = next((stage for stage in stages if stage["present"] and stage["status"] != "ok"), None)
    if failed:
        failed_stage = failed["stage"]
        reason = "startup-stage-failed"

    health = by_stage.get("health")
    health_ms = health.get("elapsedMs") if health else None
    if not failed_stage and not isinstance(health_ms, int):
        failed_stage = "health"
        reason = "startup-health-timing-missing"
    elif not failed_stage and health_ms > threshold_ms:
        failed_stage = "health"
        reason = "understandable-state-timeout"

    elapsed_values = [
        int(event["elapsedMs"])
        for event in rows
        if isinstance(event.get("elapsedMs"), int)
    ]
    elapsed_ms = max(elapsed_values, default=0)
    devices_event = by_stage.get("devices")
    device_details = devices_event.get("detail", {}) if devices_event else {}
    device_rows = device_details.get("devices", []) if isinstance(device_details, Mapping) else []
    health_details = health.get("detail", {}) if health else {}
    health_value = health_details.get("health") if isinstance(health_details, Mapping) else None
    action_event = by_stage.get("next-action")
    action_details = action_event.get("detail", {}) if action_event else {}
    primary_action = action_details.get("action") if isinstance(action_details, Mapping) else None
    health_summary = health_details.get("summary", "") if isinstance(health_details, Mapping) else ""
    discovery = by_stage.get("discovery")
    discovery_details = discovery.get("detail", {}) if discovery else {}
    discovery_mode = discovery_details.get("mode") if isinstance(discovery_details, Mapping) else None
    if discovery_mode == "network-free-packaged-first-run-fixture":
        evidence_mode = "network-free-packaged-first-run-fixture"
    elif isinstance(discovery_details, Mapping) and discovery_details.get("started") is True:
        evidence_mode = "live-discovery-started"
    else:
        evidence_mode = "unclassified"

    snapshot = {
        "stage": "next-action",
        "health": health_value,
        "devices": device_rows if isinstance(device_rows, (list, tuple)) else [],
        "primaryActions": [primary_action] if primary_action else [],
        "messages": [health_summary] if health_summary else [],
    }
    result = evaluate_first_run(
        snapshot,
        elapsed_ms=health_ms if isinstance(health_ms, int) else elapsed_ms,
        deadline_ms=threshold_ms,
    ).as_dict()
    if failed_stage:
        result.update(
            status="rejected",
            stage=failed_stage,
            reasonCode=reason or "startup-stage-failed",
        )
    result.update(
        thresholdMs=threshold_ms,
        healthElapsedMs=health_ms if isinstance(health_ms, int) else None,
        latestStageElapsedMs=elapsed_ms,
        startupStages=stages,
        evidenceMode=evidence_mode,
        physicalOperationEvidence="not-collected",
    )
    return result


def read_startup_acceptance(path: str | Path, *, threshold_ms: int = THRESHOLD_MS) -> dict:
    source = Path(path)
    events = []
    if source.is_file():
        for line in source.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
    starts = [index for index, event in enumerate(events) if event.get("stage") == "main-entry"]
    if starts:
        latest_start = starts[-1]
        pid = events[latest_start].get("pid")
        invocation = events[latest_start:]
        if pid is not None:
            invocation = [event for event in invocation if event.get("pid") == pid]
        events = invocation
    return startup_acceptance_report(events, threshold_ms=threshold_ms)
