"""Calibrate and apply a locally observed controller input profile."""
from __future__ import annotations

import math
from statistics import median
from typing import Any, Mapping, Sequence


CONTROL_AXES = ("roll", "pitch", "yaw", "throttle")
_PROFILE_SCHEMA_VERSION = 1


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _validated_mapping(mapping: Any, channel_count: int) -> dict[str, dict[str, Any]]:
    if not isinstance(mapping, Mapping) or set(mapping) != set(CONTROL_AXES):
        raise ValueError("controller-mapping-invalid")

    result: dict[str, dict[str, Any]] = {}
    used_channels: set[int] = set()
    for axis in CONTROL_AXES:
        entry = mapping[axis]
        if not isinstance(entry, Mapping) or set(entry) != {"channel", "reversed"}:
            raise ValueError("controller-mapping-invalid")
        channel = entry["channel"]
        if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel < channel_count:
            raise ValueError("controller-mapping-channel-invalid")
        if channel in used_channels or not isinstance(entry["reversed"], bool):
            raise ValueError("controller-mapping-invalid")
        used_channels.add(channel)
        result[axis] = {"channel": channel, "reversed": entry["reversed"]}
    return result


def calibrate_controller(
    controller_id: str,
    samples: Sequence[Sequence[int | float]],
    mapping: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a profile only from consistent, finite observed channel samples."""
    if not isinstance(controller_id, str) or not controller_id.strip():
        raise ValueError("controller-identity-unavailable")
    if not isinstance(samples, (list, tuple)) or len(samples) < 3:
        raise ValueError("controller-calibration-samples-insufficient")

    channel_count = len(samples[0]) if isinstance(samples[0], (list, tuple)) else 0
    if channel_count < len(CONTROL_AXES):
        raise ValueError("controller-calibration-channel-count-invalid")
    frames: list[list[int | float]] = []
    for sample in samples:
        if not isinstance(sample, (list, tuple)) or len(sample) != channel_count:
            raise ValueError("controller-calibration-channel-count-invalid")
        if any(not _finite_number(value) for value in sample):
            raise ValueError("controller-calibration-sample-invalid")
        frames.append(list(sample))

    validated_mapping = _validated_mapping(mapping, channel_count)
    calibration = []
    for channel in range(channel_count):
        values = [frame[channel] for frame in frames]
        minimum, maximum = min(values), max(values)
        calibration.append({
            "minimum": minimum,
            "center": median(values),
            "maximum": maximum,
        })

    for axis in CONTROL_AXES:
        channel = validated_mapping[axis]["channel"]
        bounds = calibration[channel]
        if bounds["minimum"] >= bounds["maximum"]:
            raise ValueError("controller-calibration-range-invalid")
        if axis != "throttle" and not bounds["minimum"] < bounds["center"] < bounds["maximum"]:
            raise ValueError("controller-calibration-center-invalid")

    return {
        "schemaVersion": _PROFILE_SCHEMA_VERSION,
        "controllerId": controller_id.strip(),
        "channelCount": channel_count,
        "calibration": calibration,
        "mapping": validated_mapping,
    }


def validate_controller_profile(profile: Any) -> dict[str, Any]:
    """Return a validated copy of a stored profile or raise ``controller-profile-invalid``."""
    if not isinstance(profile, Mapping) or set(profile) != {"schemaVersion", "controllerId", "channelCount", "calibration", "mapping"}:
        raise ValueError("controller-profile-invalid")
    if profile.get("schemaVersion") != _PROFILE_SCHEMA_VERSION:
        raise ValueError("controller-profile-invalid")
    controller_id = profile.get("controllerId")
    if not isinstance(controller_id, str) or not controller_id.strip() or controller_id != controller_id.strip():
        raise ValueError("controller-profile-invalid")
    channel_count = profile.get("channelCount")
    calibration = profile.get("calibration")
    if isinstance(channel_count, bool) or not isinstance(channel_count, int) or channel_count < len(CONTROL_AXES):
        raise ValueError("controller-profile-invalid")
    if not isinstance(calibration, (list, tuple)) or len(calibration) != channel_count:
        raise ValueError("controller-profile-invalid")
    validated_calibration = []
    for bounds in calibration:
        if not isinstance(bounds, Mapping) or set(bounds) != {"minimum", "center", "maximum"}:
            raise ValueError("controller-profile-invalid")
        minimum, center, maximum = bounds["minimum"], bounds["center"], bounds["maximum"]
        if not all(_finite_number(item) for item in (minimum, center, maximum)) or not minimum <= center <= maximum:
            raise ValueError("controller-profile-invalid")
        validated_calibration.append({"minimum": minimum, "center": center, "maximum": maximum})
    try:
        mapping = _validated_mapping(profile.get("mapping"), channel_count)
    except ValueError:
        raise ValueError("controller-profile-invalid") from None
    for axis in CONTROL_AXES:
        bounds = validated_calibration[mapping[axis]["channel"]]
        if bounds["minimum"] >= bounds["maximum"]:
            raise ValueError("controller-profile-invalid")
        if axis != "throttle" and not bounds["minimum"] < bounds["center"] < bounds["maximum"]:
            raise ValueError("controller-profile-invalid")
    return {
        "schemaVersion": _PROFILE_SCHEMA_VERSION,
        "controllerId": controller_id,
        "channelCount": channel_count,
        "calibration": validated_calibration,
        "mapping": mapping,
    }


def apply_controller_profile(profile: Mapping[str, Any], channels: Sequence[int | float]) -> dict[str, float]:
    """Normalize one fresh input frame; reject stale, malformed, or out-of-range data."""
    if not isinstance(profile, Mapping) or profile.get("schemaVersion") != _PROFILE_SCHEMA_VERSION:
        raise ValueError("controller-profile-invalid")
    controller_id = profile.get("controllerId")
    if not isinstance(controller_id, str) or not controller_id.strip():
        raise ValueError("controller-profile-invalid")
    channel_count = profile.get("channelCount")
    calibration = profile.get("calibration")
    if isinstance(channel_count, bool) or not isinstance(channel_count, int) or channel_count < len(CONTROL_AXES):
        raise ValueError("controller-profile-invalid")
    if not isinstance(calibration, (list, tuple)) or len(calibration) != channel_count:
        raise ValueError("controller-profile-invalid")
    for bounds in calibration:
        if not isinstance(bounds, Mapping) or set(bounds) != {"minimum", "center", "maximum"}:
            raise ValueError("controller-profile-invalid")
        minimum, center, maximum = bounds["minimum"], bounds["center"], bounds["maximum"]
        if not all(_finite_number(item) for item in (minimum, center, maximum)) or not minimum <= center <= maximum:
            raise ValueError("controller-profile-invalid")
    mapping = _validated_mapping(profile.get("mapping"), channel_count)
    if not isinstance(channels, (list, tuple)) or len(channels) != channel_count:
        raise ValueError("controller-input-unavailable")
    if any(not _finite_number(value) for value in channels):
        raise ValueError("controller-input-invalid")

    normalized: dict[str, float] = {}
    for axis in CONTROL_AXES:
        entry = mapping[axis]
        channel = entry["channel"]
        value = channels[channel]
        bounds = calibration[channel]
        minimum, center, maximum = bounds["minimum"], bounds["center"], bounds["maximum"]
        if minimum >= maximum:
            raise ValueError("controller-profile-invalid")
        if not minimum <= value <= maximum:
            raise ValueError("controller-input-outside-calibration")
        if axis == "throttle":
            result = (value - minimum) / (maximum - minimum)
            if entry["reversed"]:
                result = 1.0 - result
        else:
            if not minimum < center < maximum:
                raise ValueError("controller-profile-invalid")
            result = (value - center) / (center - minimum) if value < center else (value - center) / (maximum - center)
            if entry["reversed"]:
                result = -result
        normalized[axis] = float(result)
    return normalized
