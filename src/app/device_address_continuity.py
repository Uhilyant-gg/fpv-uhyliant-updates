"""Accept camera address churn only from fresh matching OpenIPC identity evidence."""
from typing import Any, Mapping

def device_address_continuity(previous: Mapping[str,Any] | None, observed: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(previous,Mapping) or not isinstance(observed,Mapping): return {'health':'unknown','accepted':False,'reasonCode':'identity-evidence-unavailable'}
 if observed.get('verifiedOpenIPC') is not True: return {'health':'unknown','accepted':False,'reasonCode':'openipc-not-verified'}
 keys=('platform','sensor')
 if any(not str(previous.get(k) or '').strip() or previous.get(k)!=observed.get(k) for k in keys): return {'health':'problem','accepted':False,'reasonCode':'hardware-identity-mismatch'}
 host=str(observed.get('host') or '').strip()
 if not host: return {'health':'unknown','accepted':False,'reasonCode':'observed-address-missing'}
 return {'health':'ready','accepted':True,'host':host,'addressChanged':host!=str(previous.get('host') or '').strip(),'reasonCode':'fresh-identity-continuity'}
