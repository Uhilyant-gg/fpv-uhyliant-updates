"""Select a zero-config startup camera only when evidence is unambiguous."""
from __future__ import annotations
from typing import Any, Iterable, Mapping


def select_startup_camera(candidates: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    verified = []
    for item in candidates or ():
        if not isinstance(item, Mapping):
            continue
        host = str(item.get("host") or "").strip()
        if item.get("verified") is True and host:
            verified.append({"host": host, "id": item.get("id")})
    unique = {item["host"]: item for item in verified}
    if not unique:
        return {"selected": None, "action": "find-camera", "reasonCode": "no-verified-camera"}
    if len(unique) != 1:
        return {"selected": None, "action": None, "reasonCode": "camera-selection-ambiguous"}
    selected = next(iter(unique.values()))
    return {"selected": selected, "action": "connect-camera", "reasonCode": "single-verified-camera"}
