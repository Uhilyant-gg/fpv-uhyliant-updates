"""Deterministic repository-software contract for the first-run journey."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping


THRESHOLD_MS = 10_000
UI_STAGES = (
    "launch",
    "restore",
    "discovery",
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
    failed = next(
        (stage for stage in stages if stage["present"] and stage["status"] == "error"),
        None,
    )
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
        reason = "startup-health-over-threshold"

    elapsed_values = [
        int(event["elapsedMs"])
        for event in rows
        if isinstance(event.get("elapsedMs"), int)
    ]
    elapsed_ms = max(elapsed_values, default=0)
    ready = failed_stage is None

    if ready:
        return {
            "status": "ready",
            "stage": "health",
            "reasonCode": "first-run-software-acceptance-ready",
            "summary": "Зрозумілий стан системи показано в межах визначеного часу.",
            "thresholdMs": threshold_ms,
            "elapsedMs": health_ms,
            "latestStageElapsedMs": elapsed_ms,
            "stages": stages,
            "operation": {
                "present": "operation" in by_stage,
                "usable": False,
                "evidence": "not-collected",
            },
        }
    return {
        "status": "blocked",
        "stage": failed_stage or "health",
        "reasonCode": reason or "startup-state-unavailable",
        "summary": "Перший запуск не пройшов повну перевірку.",
        "thresholdMs": threshold_ms,
        "elapsedMs": health_ms if isinstance(health_ms, int) else elapsed_ms,
        "latestStageElapsedMs": elapsed_ms,
        "stages": stages,
        "operation": {
            "present": "operation" in by_stage,
            "usable": False,
            "evidence": "not-collected",
        },
    }


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
