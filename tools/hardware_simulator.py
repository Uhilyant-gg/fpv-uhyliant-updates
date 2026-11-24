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


def simulate(state: VirtualDeviceState, event: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic synthetic evidence without firmware/network I/O."""
    kind = event.get("type")
    if kind == "observe":
        next_state = state
        reason = "observed"
    elif kind == "set-reachable" and isinstance(event.get("value"), bool):
        next_state = VirtualDeviceState(**{**asdict(state), "reachable": event["value"]})
        reason = "reachability-simulated"
    elif kind == "verify-identity" and event.get("verified") is True:
        next_state = VirtualDeviceState(**{**asdict(state), "identity_verified": True})
        reason = "identity-simulated"
    else:
        return {
            "status": "unknown",
            "reasonCode": "unsupported-simulator-event",
            "evidenceKind": "simulation",
            "physicalEvidenceComplete": False,
            "state": asdict(state),
        }
    return {
        "status": "ready",
        "reasonCode": reason,
        "evidenceKind": "simulation",
        "physicalEvidenceComplete": False,
        "state": asdict(next_state),
    }
