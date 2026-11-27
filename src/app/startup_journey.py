"""Bounded presentation contract for the zero-config operator journey."""

from __future__ import annotations
from typing import Any, Mapping


def startup_journey(startup: Mapping[str, Any] | None) -> dict[str, Any]:
    stages = ('discover', 'restore', 'camera', 'video', 'operate')
    if not isinstance(startup, Mapping):
        return {
            'health': 'unknown',
            'stage': 'discover',
            'step': 1,
            'total': len(stages),
            'action': 'find-camera',
            'reasonCode': 'startup-state-unavailable',
        }
    stage = startup.get('stage') if startup.get('stage') in stages else 'discover'
    health = (
        startup.get('health') if startup.get('health') in {'ready', 'attention', 'problem', 'unknown'} else 'unknown'
    )
    if stage == 'operate' and health != 'ready':
        stage = 'video'
    return {
        'health': health,
        'stage': stage,
        'step': stages.index(stage) + 1,
        'total': len(stages),
        'action': startup.get('action'),
        'reasonCode': startup.get('reasonCode') or 'startup-state-unknown',
    }
