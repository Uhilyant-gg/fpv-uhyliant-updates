"""Summarize persisted and discovered camera candidates for zero-config startup."""
from __future__ import annotations
from typing import Any, Iterable, Mapping


def discovery_startup_summary(saved: Iterable[Mapping[str, Any]] | None, discovered: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
    saved_hosts={str(x.get('host') or '').strip() for x in (saved or ()) if isinstance(x,Mapping) and x.get('host')}
    verified={str(x.get('host') or '').strip() for x in (discovered or ()) if isinstance(x,Mapping) and x.get('openipc') is True and x.get('identityVerified') is True and x.get('host')}
    verified.discard('')
    if len(verified)==1:
        host=next(iter(verified));return {'health':'ready','action':'connect-camera','host':host,'reasonCode':'single-verified-discovery','restored':host in saved_hosts}
    if len(verified)>1:return {'health':'attention','action':None,'host':None,'reasonCode':'verified-camera-ambiguity','restored':False}
    return {'health':'unknown','action':'find-camera','host':None,'reasonCode':'verified-camera-unavailable','restored':False}
