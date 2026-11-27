"""Fail-closed video runtime health composed from continuity and observed playback."""

from typing import Any, Mapping


def video_runtime_health(continuity: Mapping[str, Any] | None, runtime: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(runtime, Mapping):
        return {'health': 'unknown', 'action': None, 'reasonCode': 'playback-unobserved'}
    state = runtime.get('state')
    if state in ('stalled', 'error'):
        return {'health': 'problem', 'action': 'reconnect-video', 'reasonCode': 'playback-' + str(state)}
    if state != 'playing':
        return {'health': 'unknown', 'action': None, 'reasonCode': 'playback-not-confirmed'}
    if not isinstance(continuity, Mapping) or continuity.get('continuous') is not True:
        return {'health': 'attention', 'action': 'reconnect-video', 'reasonCode': 'stream-continuity-unconfirmed'}
    return {'health': 'ready', 'action': None, 'reasonCode': 'video-playing-continuously'}
