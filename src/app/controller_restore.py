"""Restore saved controller metadata only after fresh matching observation and input health."""
from typing import Any, Mapping
from controller_input_health import controller_input_health


def controller_restore(saved: Mapping[str,Any] | None, observed: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(observed,Mapping): return {'health':'unknown','restored':False,'inputHealth':'unknown','reasonCode':'controller-not-observed'}
 if not isinstance(saved,Mapping): return {'health':'attention','restored':False,'inputHealth':'unknown','reasonCode':'controller-profile-unavailable'}
 if not saved.get('id') or observed.get('id')!=saved.get('id'): return {'health':'unknown','restored':False,'inputHealth':'unknown','reasonCode':'controller-identity-mismatch'}
 if observed.get('connected') is not True: return {'health':'unknown','restored':False,'inputHealth':'unknown','reasonCode':'controller-not-observed'}
 inputs=controller_input_health(observed)
 if inputs.get('health')!='ready':
  return {'health':inputs.get('health','unknown'),'restored':False,'inputHealth':inputs.get('health','unknown'),'reasonCode':inputs.get('reasonCode','controller-input-unavailable')}
 return {'health':'ready','restored':True,'inputHealth':'ready','channelCount':inputs.get('channelCount'),'reasonCode':'controller-observed-inputs-and-restored'}
