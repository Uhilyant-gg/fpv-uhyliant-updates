"""In-flight alerts from fresh telemetry against operator-configured thresholds.

Only fresh, known values can raise an alert; stale or missing values never do
(lost telemetry is its own alert). A threshold of 0 disables that alert. The
per-cell voltage alert needs the operator to set the cell count: it is never
guessed from the pack voltage.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

# name -> (default, minimum, maximum, integer)
THRESHOLD_SPEC = {
    "linkQualityMin": (50, 0, 100, True),
    "batteryRemainingMin": (20, 0, 100, True),
    "cellVoltageMin": (3.5, 0.0, 4.2, False),
    "cellCount": (0, 0, 12, True),
}
DEFAULT_THRESHOLDS = {name: spec[0] for name, spec in THRESHOLD_SPEC.items()}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def validate_threshold(name: str, value: Any) -> int | float:
    """Return the normalized value or raise ValueError("alert-threshold-invalid")."""
    if name not in THRESHOLD_SPEC:
        raise ValueError("alert-threshold-invalid")
    _, low, high, integer = THRESHOLD_SPEC[name]
    number = _number(value)
    if number is None or not low <= number <= high:
        raise ValueError("alert-threshold-invalid")
    if integer:
        if number != int(number):
            raise ValueError("alert-threshold-invalid")
        return int(number)
    return round(number, 2)


def validate_thresholds(values: Any) -> dict[str, int | float]:
    """Merge stored values over defaults; any invalid entry falls back to its default."""
    result = dict(DEFAULT_THRESHOLDS)
    if isinstance(values, Mapping):
        for name in THRESHOLD_SPEC:
            if name in values:
                try:
                    result[name] = validate_threshold(name, values[name])
                except ValueError:
                    pass
    return result


def _fresh(telemetry: Mapping[str, Any], field: str) -> float | None:
    if (telemetry.get("freshness") or {}).get(field) is False:
        return None
    return _number(telemetry.get(field))


def evaluate_alerts(telemetry: Mapping[str, Any] | None, thresholds: Mapping[str, Any] | None) -> list[dict[str, str]]:
    """Return active alerts, most severe first: {"code", "level", "text"}."""
    if not isinstance(telemetry, Mapping):
        return []
    limits = validate_thresholds(thresholds)
    if telemetry.get("connected") is False:
        return [{"code": "telemetry-lost", "level": "critical", "text": "Телеметрію втрачено"}]
    if telemetry.get("connected") is not True:
        return []

    alerts: list[dict[str, str]] = []
    quality = _fresh(telemetry, "linkQuality")
    if limits["linkQualityMin"] and quality is not None and quality < limits["linkQualityMin"]:
        alerts.append(
            {"code": "link-quality-low", "level": "critical", "text": f"Слабкий радіолінк: LQ {quality:.0f}%"}
        )

    voltage = _fresh(telemetry, "batteryVoltage")
    cells = limits["cellCount"]
    if limits["cellVoltageMin"] and cells and voltage is not None:
        per_cell = voltage / cells
        if per_cell < limits["cellVoltageMin"]:
            alerts.append(
                {"code": "cell-voltage-low", "level": "critical", "text": f"Низька напруга: {per_cell:.2f} В на банку"}
            )

    remaining = _fresh(telemetry, "batteryRemaining")
    if limits["batteryRemainingMin"] and remaining is not None and remaining < limits["batteryRemainingMin"]:
        alerts.append({"code": "battery-remaining-low", "level": "warning", "text": f"Низький заряд: {remaining:.0f}%"})
    return alerts
