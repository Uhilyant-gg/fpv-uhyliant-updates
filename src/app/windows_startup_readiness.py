"""Fail-closed readiness summary for packaged Windows startup evidence."""

from __future__ import annotations
from typing import Any, Iterable, Mapping

REQUIRED = (
    'python-runtime',
    'pyside-core',
    'pyside-gui',
    'pyside-qml',
    'pyside-quick',
    'pyside-controls',
    'pyside-multimedia',
    'pyside-serial',
    'paramiko',
)


def windows_startup_readiness(events: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    completed = {str(x.get('stage')) for x in (events or ()) if isinstance(x, Mapping) and x.get('status') == 'ok'}
    failed = [str(x.get('stage')) for x in (events or ()) if isinstance(x, Mapping) and x.get('status') == 'error']
    if failed:
        return {'health': 'problem', 'missing': [], 'failed': failed, 'reasonCode': 'startup-probe-failed'}
    missing = [name for name in REQUIRED if name + '-complete' not in completed]
    if missing:
        return {'health': 'unknown', 'missing': missing, 'failed': [], 'reasonCode': 'startup-probes-incomplete'}
    return {'health': 'ready', 'missing': [], 'failed': [], 'reasonCode': 'startup-probes-complete'}
