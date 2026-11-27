"""Validate observed RC input quality without synthesizing channels."""

from __future__ import annotations
import math
from typing import Any, Mapping


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def controller_input_health(observed: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(observed, Mapping) or observed.get('connected') is not True:
        return {'health': 'unknown', 'reasonCode': 'controller-not-observed', 'channelCount': None}
    channels = observed.get('channels')
    if not isinstance(channels, (list, tuple)) or not channels:
        return {'health': 'unknown', 'reasonCode': 'controller-input-unavailable', 'channelCount': None}
    if any(not _finite_number(value) for value in channels):
        return {'health': 'problem', 'reasonCode': 'controller-input-invalid', 'channelCount': len(channels)}
    return {'health': 'ready', 'reasonCode': 'controller-input-observed', 'channelCount': len(channels)}
