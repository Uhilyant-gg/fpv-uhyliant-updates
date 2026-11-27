"""Compose canonical runtime health, zero-config readiness and Next Best Action."""

from __future__ import annotations

from typing import Any, Mapping

from device_health import device_health
from next_best_action import select_next_best_action
from station_health import station_health
from vehicle_health import vehicle_health
from zero_config_readiness import zero_config_readiness


def runtime_health_snapshot(
    *,
    device: Mapping[str, Any] | None,
    vehicle_snapshot: Mapping[str, Any] | None,
    vehicle_diagnostics: Mapping[str, Any] | None,
    workspace: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return health boundaries plus presentation-only startup and next-action state."""
    camera = device_health(device)
    vehicle = vehicle_health(vehicle_snapshot, vehicle_diagnostics)
    station = station_health((camera, vehicle))
    components = {
        "camera": camera.as_dict(),
        "vehicle": vehicle.as_dict(),
        "station": station.as_dict(),
    }
    next_action = select_next_best_action(
        {
            "camera": components["camera"],
            "vehicle": components["vehicle"],
        }
    )
    startup = zero_config_readiness(components["camera"], workspace)
    return {
        **components,
        "nextBestAction": next_action.as_dict(),
        "zeroConfigStartup": startup,
    }
