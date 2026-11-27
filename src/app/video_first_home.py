"""Presentation-only video-first home and one contextual action."""

from typing import Any, Mapping

_ALLOWED = {'ready', 'attention', 'problem', 'unknown'}


def video_first_home(camera: Mapping[str, Any] | None, startup: Mapping[str, Any] | None) -> dict[str, Any]:
    health = (camera or {}).get('health', 'unknown') if isinstance(camera, Mapping) else 'unknown'
    if health not in _ALLOWED:
        health = 'unknown'
    usable = isinstance(camera, Mapping) and camera.get('usable') is True and health == 'ready'
    action = (startup or {}).get('action') if isinstance(startup, Mapping) else None
    return {
        'home': 'video' if usable else 'startup',
        'health': health,
        'nextBestAction': action,
        'authority': 'presentation-only',
    }
