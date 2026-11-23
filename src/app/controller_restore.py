"""Restore saved controller metadata only after fresh matching observation."""
from typing import Any, Mapping

def controller_restore(saved: Mapping[str,Any] | None, observed: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(observed,Mapping): return {'health':'unknown','restored':False,'reasonCode':'controller-not-observed'}
 if not isinstance(saved,Mapping): return {'health':'attention','restored':False,'reasonCode':'controller-profile-unavailable'}
 if not saved.get('id') or observed.get('id')!=saved.get('id'): return {'health':'unknown','restored':False,'reasonCode':'controller-identity-mismatch'}
 if observed.get('connected') is not True or not observed.get('channels'): return {'health':'unknown','restored':False,'reasonCode':'controller-input-unavailable'}
 return {'health':'ready','restored':True,'reasonCode':'controller-observed-and-restored'}
