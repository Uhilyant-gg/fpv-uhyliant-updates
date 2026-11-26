"""Deterministic acceptance contract for the normal first-run journey."""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable, Iterable, Mapping

STAGES = ("launch", "discovery", "health", "devices", "next-action", "operation")
HEALTH = {"ready", "attention", "problem", "unknown"}
TECHNICAL_MARKERS = (
    "traceback", "exception", "connection refused", "socket error", "rtsp timeout",
    "ssh transport", "errno", "stack trace",
)


@dataclass(frozen=True)
class AcceptanceResult:
    status: str
    elapsedMs: int
    stage: str
    reasonCode: str
    health: str
    deviceCount: int
    primaryAction: str | None
    manualConfigRequired: bool
    technicalMessageExposed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "elapsedMs": self.elapsedMs,
            "stage": self.stage,
            "reasonCode": self.reasonCode,
            "health": self.health,
            "deviceCount": self.deviceCount,
            "primaryAction": self.primaryAction,
            "manualConfigRequired": self.manualConfigRequired,
            "technicalMessageExposed": self.technicalMessageExposed,
        }


def _technical_message(messages: Iterable[Any]) -> bool:
    text = " ".join(str(item).lower() for item in messages if item is not None)
    return any(marker in text for marker in TECHNICAL_MARKERS)


def evaluate_first_run(
    snapshot: Mapping[str, Any] | None,
    *,
    elapsed_ms: int,
    deadline_ms: int = 10_000,
) -> AcceptanceResult:
    data = snapshot if isinstance(snapshot, Mapping) else {}
    stage = data.get("stage") if data.get("stage") in STAGES else "launch"
    health = data.get("health") if data.get("health") in HEALTH else "unknown"
    devices = data.get("devices") if isinstance(data.get("devices"), (list, tuple)) else ()
    actions = data.get("primaryActions") if isinstance(data.get("primaryActions"), (list, tuple)) else ()
    actions = tuple(str(action) for action in actions if action)
    manual = bool(data.get("manualConfigRequired", False) or data.get("terminalRequired", False))
    technical = _technical_message(data.get("messages", ()))

    reason = "first-run-accepted"
    status = "accepted"
    failed_stage = stage
    if elapsed_ms > deadline_ms:
        status, reason = "rejected", "understandable-state-timeout"
        failed_stage = "health"
    elif manual:
        status, reason = "rejected", "manual-configuration-required"
    elif technical:
        status, reason = "rejected", "technical-message-exposed"
    elif len(actions) > 1:
        status, reason = "rejected", "multiple-primary-actions"
        failed_stage = "next-action"
    elif stage == "operation" and health != "ready":
        status, reason = "rejected", "operation-not-ready"
    elif stage != "operation" and not actions:
        status, reason = "rejected", "recovery-action-missing"
        failed_stage = "next-action"

    return AcceptanceResult(
        status=status,
        elapsedMs=max(0, int(elapsed_ms)),
        stage=failed_stage,
        reasonCode=reason,
        health=health,
        deviceCount=len(devices),
        primaryAction=actions[0] if len(actions) == 1 else None,
        manualConfigRequired=manual,
        technicalMessageExposed=technical,
    )


def run_first_run_acceptance(
    snapshot_provider: Callable[[], Mapping[str, Any]],
    *,
    clock: Callable[[], float] = monotonic,
    deadline_ms: int = 10_000,
) -> dict[str, Any]:
    started = clock()
    snapshot = snapshot_provider()
    elapsed_ms = round((clock() - started) * 1000)
    return evaluate_first_run(snapshot, elapsed_ms=elapsed_ms, deadline_ms=deadline_ms).as_dict()
