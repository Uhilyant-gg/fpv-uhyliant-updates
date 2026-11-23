"""Validate observed RC input quality without synthesizing channels."""
from __future__ import annotations
from typing import Any, Mapping

def controller_input_health(observed: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(observed,Mapping) or observed.get('connected') is not True:return {'health':'unknown','reasonCode':'controller-not-observed','channelCount':None}
 channels=observed.get('channels')
 if not isinstance(channels,(list,tuple)) or not channels:return {'health':'unknown','reasonCode':'controller-input-unavailable','channelCount':None}
 if any(not isinstance(v,(int,float)) for v in channels):return {'health':'problem','reasonCode':'controller-input-invalid','channelCount':len(channels)}
 return {'health':'ready','reasonCode':'controller-input-observed','channelCount':len(channels)}
