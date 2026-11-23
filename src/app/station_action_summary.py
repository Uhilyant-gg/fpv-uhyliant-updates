"""Station-level summary of an already selected Next Best Action."""
from __future__ import annotations
from typing import Any, Mapping


def station_action_summary(next_action: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(next_action, Mapping) or not isinstance(next_action.get("action"), str):
        return {"hasAction": False, "action": None, "source": None, "reasonCode": "no-safe-action"}
    return {
        "hasAction": True,
        "action": next_action["action"],
        "source": next_action.get("source") if isinstance(next_action.get("source"), str) else None,
        "reasonCode": next_action.get("reasonCode") if isinstance(next_action.get("reasonCode"), str) else "safe-action-selected",
    }
