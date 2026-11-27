"""Select a zero-config startup camera only when evidence is unambiguous."""

from __future__ import annotations
from typing import Any, Iterable, Mapping


def select_startup_camera(candidates: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    usable = []
    for item in candidates or ():
        if not isinstance(item, Mapping):
            continue
        host = str(item.get("host") or "").strip()
        evidence = tuple(str(x) for x in (item.get("evidence") or ()) if x)
        verified = item.get("verified") is True and "verified-openipc" in evidence
        if verified and host:
            usable.append({"host": host, "id": item.get("id"), "evidence": list(evidence)})
    unique = {item["host"]: item for item in usable}
    if not unique:
        return {"health": "unknown", "selected": None, "action": "find-camera", "reasonCode": "no-verified-camera"}
    if len(unique) != 1:
        return {"health": "attention", "selected": None, "action": None, "reasonCode": "camera-selection-ambiguous"}
    selected = next(iter(unique.values()))
    return {"health": "ready", "selected": selected, "action": "connect-camera", "reasonCode": "single-verified-camera"}
