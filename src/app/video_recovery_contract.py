"""Recovery contract: source changes invalidate preparation and reconnect is not playback success."""
from typing import Any, Mapping

def video_recovery_contract(before: Mapping[str,Any] | None, after: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(after,Mapping): return {'health':'unknown','prepared':False,'reasonCode':'runtime-evidence-unavailable'}
 changed=isinstance(before,Mapping) and before.get('sourceFingerprint')!=after.get('sourceFingerprint')
 if changed: return {'health':'attention','prepared':False,'action':'prepare-video','reasonCode':'video-input-changed'}
 state=after.get('state')
 if state in ('stalled','error'): return {'health':'problem','prepared':True,'action':'reconnect-video','reasonCode':'video-recovery-required'}
 if state in ('ready','reconnecting'): return {'health':'attention','prepared':True,'action':None,'reasonCode':'fresh-playback-required'}
 if state=='playing' and after.get('freshPlayback') is True: return {'health':'ready','prepared':True,'action':None,'reasonCode':'fresh-playback-observed'}
 return {'health':'unknown','prepared':False,'action':None,'reasonCode':'video-runtime-unverified'}
