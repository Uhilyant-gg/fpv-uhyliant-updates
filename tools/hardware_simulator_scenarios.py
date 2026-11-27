"""Deterministic scenario/recovery helpers for the side-effect-free E6 simulator."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from hardware_simulator import VirtualDeviceState, simulate


def select_device(devices: Iterable[VirtualDeviceState]) -> dict[str, Any]:
    candidates = list(devices)
    if not candidates:
        return {
            "status": "unknown",
            "reasonCode": "no-simulated-device",
            "selectedDeviceId": None,
            "evidenceKind": "simulation",
            "physicalEvidenceComplete": False,
        }
    if len(candidates) != 1:
        return {
            "status": "unknown",
            "reasonCode": "simulated-device-ambiguous",
            "selectedDeviceId": None,
            "evidenceKind": "simulation",
            "physicalEvidenceComplete": False,
        }
    return {
        "status": "ready",
        "reasonCode": "single-simulated-device",
        "selectedDeviceId": candidates[0].device_id,
        "evidenceKind": "simulation",
        "physicalEvidenceComplete": False,
    }


def retry_update(state: VirtualDeviceState, retry_count: int, retry_budget: int) -> dict[str, Any]:
    if not isinstance(retry_count, int) or not isinstance(retry_budget, int) or retry_count < 0 or retry_budget < 0:
        return _invalid(state, "malformed-retry-budget")
    if retry_count >= retry_budget:
        return _invalid(state, "update-retry-budget-exhausted", "problem")
    if not state.update_failed or state.update_active or not state.reachable or state.rebooting:
        return _invalid(state, "update-retry-invalid-state")
    clean = VirtualDeviceState(**{**asdict(state), "update_failed": False})
    return simulate(clean, {"type": "start-update"})


def replay(initial: VirtualDeviceState, events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    state = initial
    trace = []
    try:
        event_list = list(events)
    except (TypeError, ValueError):
        return _invalid(initial, "malformed-scenario")
    for index, event in enumerate(event_list):
        if not isinstance(event, Mapping) or not isinstance(event.get("type"), str):
            result = _invalid(state, "malformed-scenario-event")
        else:
            result = simulate(state, event)
        trace.append({"index": index, "reasonCode": result["reasonCode"], "status": result["status"]})
        state = VirtualDeviceState(**result["state"])
        if result["status"] == "problem" or result["reasonCode"] in {
            "unsupported-simulator-event",
            "malformed-scenario-event",
        }:
            return {**result, "trace": trace, "stoppedAt": index}
    return {
        "status": "ready" if state.evidence_fresh else "unknown",
        "reasonCode": "scenario-complete",
        "state": asdict(state),
        "trace": trace,
        "stoppedAt": None,
        "evidenceKind": "simulation",
        "physicalEvidenceComplete": False,
    }


def validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, VirtualDeviceState):
        return {
            "status": "unknown",
            "reasonCode": "malformed-virtual-state",
            "evidenceKind": "simulation",
            "physicalEvidenceComplete": False,
        }
    if (
        not state.device_id
        or state.rebooting
        and not state.reachable
        and state.update_active
        or state.update_active
        and state.update_failed
    ):
        return _invalid(state, "contradictory-virtual-state")
    return {
        "status": "ready",
        "reasonCode": "virtual-state-valid",
        "state": asdict(state),
        "evidenceKind": "simulation",
        "physicalEvidenceComplete": False,
    }


def _invalid(state: VirtualDeviceState, reason: str, status: str = "unknown") -> dict[str, Any]:
    return {
        "status": status,
        "reasonCode": reason,
        "state": asdict(state),
        "evidenceKind": "simulation",
        "physicalEvidenceComplete": False,
    }
