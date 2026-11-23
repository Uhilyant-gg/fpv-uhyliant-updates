"""Read-only presentation summary for normalized telemetry."""
from __future__ import annotations
from typing import Any, Mapping


def telemetry_health_summary(telemetry: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(telemetry, Mapping):
        return {"health":"unknown","provider":None,"reasonCode":"telemetry-evidence-unavailable"}
    connected=telemetry.get("connected")
    provider=telemetry.get("provider") if isinstance(telemetry.get("provider"),str) else None
    if connected is True:health="ready";reason="telemetry-connected"
    elif connected is False:health="attention";reason="telemetry-disconnected"
    else:health="unknown";reason="telemetry-connection-unknown"
    return {"health":health,"provider":provider,"reasonCode":reason}
