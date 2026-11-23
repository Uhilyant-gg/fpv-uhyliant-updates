"""User-facing presentation for deterministic Next Best Action results.

Presentation never invents an action. Unknown or absent actions remain unavailable.
"""
from __future__ import annotations

from typing import Any, Mapping

_LABELS = {
    "diagnose": "Діагностувати",
    "find-camera": "Знайти камеру",
    "identify-camera": "Визначити камеру",
    "refresh-identity": "Оновити ідентифікацію",
    "verify-camera": "Перевірити камеру",
    "show-video": "Показати відео",
}


def present_next_action(next_action: Mapping[str, Any] | None) -> dict[str, Any]:
    """Translate a selected action into stable UI data without adding authority."""
    if not isinstance(next_action, Mapping):
        return {"available": False, "action": None, "label": "", "source": None, "reasonCode": "next-action-unavailable"}

    action = next_action.get("action")
    if action not in _LABELS:
        return {"available": False, "action": None, "label": "", "source": next_action.get("source"), "reasonCode": "next-action-unavailable"}

    return {
        "available": True,
        "action": action,
        "label": _LABELS[action],
        "source": next_action.get("source"),
        "reasonCode": next_action.get("reasonCode") or "safe-action-selected",
    }
