"""Station settings that make up a vehicle preset: OSD layout/style and alert thresholds.

Pure validation shared by the Station (Qt) object and the preset store, so a
preset file from disk or from another computer is checked the same way as a
value set from the UI.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from flight_alerts import THRESHOLD_SPEC, validate_threshold

ELEMENT_NAMES = (
    "link",
    "arm",
    "mode",
    "battery",
    "gps",
    "altitude",
    "speed",
    "heading",
    "video",
    "homeDistance",
    "reticle",
    "horizon",
)
POSITIONS = ("top-left", "top-right", "bottom-left", "bottom-right")
DEFAULT_ELEMENT_VISIBILITY = {name: True for name in ELEMENT_NAMES}
DEFAULT_ELEMENT_VISIBILITY.update({"homeDistance": False, "reticle": False, "horizon": False})
DEFAULT_OPACITY = 0.58
DEFAULT_SCALE = 1.0
DEFAULT_POSITION = "top-left"


def default_settings() -> dict[str, Any]:
    return {
        "osd": {
            "enabled": True,
            "opacity": DEFAULT_OPACITY,
            "scale": DEFAULT_SCALE,
            "position": DEFAULT_POSITION,
            "elements": {},
            "elementVisibility": dict(DEFAULT_ELEMENT_VISIBILITY),
        },
        "alerts": {name: spec[0] for name, spec in THRESHOLD_SPEC.items()},
    }


def _number(value: Any, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("station-settings-invalid")
    if not low <= float(value) <= high:
        raise ValueError("station-settings-invalid")
    return float(value)


def validate_station_settings(value: Any) -> dict[str, Any]:
    """Return a complete, normalized settings dict or raise ValueError.

    Missing keys take defaults (older files stay usable); unknown keys are
    ignored; a present but invalid value rejects the whole settings object.
    """
    if not isinstance(value, Mapping):
        raise ValueError("station-settings-invalid")
    result = default_settings()
    osd = value.get("osd", {})
    alerts = value.get("alerts", {})
    if not isinstance(osd, Mapping) or not isinstance(alerts, Mapping):
        raise ValueError("station-settings-invalid")

    out = result["osd"]
    if "enabled" in osd:
        if not isinstance(osd["enabled"], bool):
            raise ValueError("station-settings-invalid")
        out["enabled"] = osd["enabled"]
    if "opacity" in osd:
        out["opacity"] = _number(osd["opacity"], 0.0, 1.0)
    if "scale" in osd:
        out["scale"] = _number(osd["scale"], 0.85, 1.3)
    if "position" in osd:
        if osd["position"] not in POSITIONS:
            raise ValueError("station-settings-invalid")
        out["position"] = osd["position"]
    if "elements" in osd:
        elements = osd["elements"]
        if not isinstance(elements, Mapping):
            raise ValueError("station-settings-invalid")
        for name, position in elements.items():
            if name not in ELEMENT_NAMES:
                continue
            if (
                not isinstance(position, (list, tuple))
                or len(position) != 2
                or not all(type(n) is int and 0 <= n <= 100 for n in position)
            ):
                raise ValueError("station-settings-invalid")
            out["elements"][name] = [position[0], position[1]]
    if "elementVisibility" in osd:
        visibility = osd["elementVisibility"]
        if not isinstance(visibility, Mapping):
            raise ValueError("station-settings-invalid")
        for name, shown in visibility.items():
            if name not in ELEMENT_NAMES:
                continue
            if not isinstance(shown, bool):
                raise ValueError("station-settings-invalid")
            out["elementVisibility"][name] = shown

    for name in THRESHOLD_SPEC:
        if name in alerts:
            try:
                result["alerts"][name] = validate_threshold(name, alerts[name])
            except ValueError:
                raise ValueError("station-settings-invalid") from None
    return result
