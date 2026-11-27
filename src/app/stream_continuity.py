"""Evidence-only video stream continuity decision."""

from __future__ import annotations
from typing import Any, Mapping


def stream_continuity(previous: Mapping[str, Any] | None, current: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
        return {'health': 'unknown', 'action': None, 'reasonCode': 'stream-evidence-unavailable'}
    old = str(previous.get('primaryId') or '')
    new = str(current.get('primaryId') or '')
    if not new:
        return {
            'health': 'problem' if old else 'unknown',
            'action': 'reconnect-video' if old else 'show-video',
            'reasonCode': 'primary-stream-lost' if old else 'primary-stream-unavailable',
        }
    if old and old != new:
        return {'health': 'attention', 'action': 'show-video', 'reasonCode': 'primary-stream-changed'}
    return {'health': 'ready', 'action': None, 'reasonCode': 'primary-stream-continuous'}
