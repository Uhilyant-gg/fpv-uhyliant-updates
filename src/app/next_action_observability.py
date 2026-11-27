"""Sanitized observability records for Next Best Action decisions."""

from __future__ import annotations

from typing import Any, Mapping


def next_action_record(next_action: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a bounded record without copying arbitrary evidence or secrets."""
    if not isinstance(next_action, Mapping):
        return {
            "selected": False,
            "action": None,
            "source": None,
            "reasonCode": "next-action-unavailable",
        }

    action = next_action.get("action")
    source = next_action.get("source")
    reason = next_action.get("reasonCode")
    return {
        "selected": isinstance(action, str) and bool(action),
        "action": action if isinstance(action, str) else None,
        "source": source if isinstance(source, str) else None,
        "reasonCode": reason if isinstance(reason, str) and reason else "next-action-unavailable",
    }
