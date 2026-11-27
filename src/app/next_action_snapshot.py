"""Validation boundary for serialized Next Best Action snapshots."""

from __future__ import annotations

from typing import Any, Mapping

_ALLOWED_KEYS = frozenset({"action", "reasonCode", "source"})


def validated_next_action_snapshot(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize the public NBA shape while failing closed on malformed values."""
    if not isinstance(value, Mapping):
        return {"action": None, "reasonCode": "next-action-unavailable", "source": None}

    action = value.get("action")
    reason = value.get("reasonCode")
    source = value.get("source")
    if action is not None and not isinstance(action, str):
        action = None
    if source is not None and not isinstance(source, str):
        source = None
    if not isinstance(reason, str) or not reason:
        reason = "next-action-unavailable"

    return {"action": action, "reasonCode": reason, "source": source}


def is_canonical_next_action_shape(value: Mapping[str, Any] | None) -> bool:
    """Return True only for the exact public NBA schema."""
    return isinstance(value, Mapping) and set(value) == _ALLOWED_KEYS and value == validated_next_action_snapshot(value)
