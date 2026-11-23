"""Compose a canonical E2 runtime health snapshot from observed component inputs."""
from __future__ import annotations

from typing import Any, Mapping

from device_health import device_health
from station_health import station_health
from vehicle_health import vehicle_health


def runtime_health_snapshot(
    *,
    device: Mapping[str, Any] | None,
    vehicle_snapshot: Mapping[str, Any] | None,
    vehicle_diagnostics: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Return camera, vehicle, and station health using the same canonical schema."""
    camera = device_health(device)
    vehicle = vehicle_health(vehicle_snapshot, vehicle_diagnostics)
    station = station_health((camera, vehicle))
    return {
        "camera": camera.as_dict(),
        "vehicle": vehicle.as_dict(),
        "station": station.as_dict(),
    }
