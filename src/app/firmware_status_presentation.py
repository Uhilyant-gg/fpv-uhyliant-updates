"""Normal-mode presentation of firmware acquisition state without granting update authority."""
from __future__ import annotations
from typing import Any, Mapping


def firmware_status(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"state":"unknown","ready":False,"summary":"Немає підтверджених даних про прошивку.","action":None}
    state=value.get("state") if isinstance(value.get("state"),str) else "unknown"
    selection=value.get("selection") if isinstance(value.get("selection"),Mapping) else {}
    ready=state=="verified" and selection.get("ready") is True and isinstance(selection.get("artifact"),Mapping)
    reason=value.get("reason") if isinstance(value.get("reason"),str) else ""
    summary="Перевірене оновлення готове." if ready else (reason or "Оновлення ще не підтверджене.")
    return {"state":state,"ready":ready,"summary":summary,"action":"update" if ready else None}
