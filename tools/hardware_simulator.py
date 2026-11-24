"""Deterministic, side-effect-free virtual hardware state for E6 tests."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class VirtualDeviceState:
    device_id: str
    reachable: bool = True
    identity_verified: bool = False
    firmware_version: str | None = None
    rebooting: bool = False
    evidence_fresh: bool = False


def _result(state: VirtualDeviceState, reason: str, status: str = "ready") -> dict[str, Any]:
    return {
        "status": status,
        "reasonCode": reason,
        "evidenceKind": "simulation",
        "physicalEvidenceComplete": False,
        "state": asdict(state),
    }


def simulate(state: VirtualDeviceState, event: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic synthetic evidence without firmware/network I/O."""
    kind = event.get("type")
    values = asdict(state)

    if kind == "observe":
        return _result(state, "observed")
    if kind == "set-reachable" and isinstance(event.get("value"), bool):
        values.update(reachable=event["value"], evidence_fresh=False)
        return _result(VirtualDeviceState(**values), "reachability-simulated")
    if kind == "verify-identity" and event.get("verified") is True:
        if not state.reachable or state.rebooting:
            return _result(state, "identity-verification-unavailable", "unknown")
        values.update(identity_verified=True, evidence_fresh=True)
        return _result(VirtualDeviceState(**values), "identity-simulated")
    if kind == "disconnect":
        values.update(reachable=False, evidence_fresh=False)
        return _result(VirtualDeviceState(**values), "disconnected-simulated", "unknown")
    if kind == "reconnect":
        values.update(reachable=True, rebooting=False, evidence_fresh=False)
        return _result(VirtualDeviceState(**values), "reconnected-revalidation-required", "unknown")
    if kind == "start-reboot" and state.reachable and not state.rebooting:
        values.update(rebooting=True, evidence_fresh=False)
        return _result(VirtualDeviceState(**values), "reboot-started-simulated", "unknown")
    if kind == "reboot-unreachable" and state.rebooting:
        values.update(reachable=False, evidence_fresh=False)
        return _result(VirtualDeviceState(**values), "reboot-unreachable-simulated", "unknown")
    if kind == "reboot-reachable" and state.rebooting:
        values.update(reachable=True, rebooting=False, evidence_fresh=False)
        return _result(VirtualDeviceState(**values), "reboot-revalidation-required", "unknown")
    if kind == "reboot-timeout" and state.rebooting:
        values.update(reachable=False, evidence_fresh=False)
        return _result(VirtualDeviceState(**values), "reboot-timeout-simulated", "problem")
    return _result(state, "unsupported-simulator-event", "unknown")
