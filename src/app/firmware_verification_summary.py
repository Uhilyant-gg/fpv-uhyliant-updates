"""Presentation-only summary for guarded post-update verification evidence."""
from __future__ import annotations
from typing import Any, Mapping

def firmware_verification_summary(status: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(status,Mapping):return {'health':'unknown','stage':'verification','reasonCode':'verification-evidence-unavailable'}
 state=status.get('state');verification=status.get('verification') if isinstance(status.get('verification'),Mapping) else {}
 if state=='verified' and verification.get('ok') is True and str(verification.get('observedFirmware') or verification.get('firmware') or '').strip():return {'health':'ready','stage':'verified','reasonCode':'post-update-verified'}
 if state in {'reboot-pending','rediscovering'}:return {'health':'attention','stage':state,'reasonCode':'post-update-pending'}
 if state=='error':return {'health':'problem','stage':'verification','reasonCode':'post-update-verification-failed'}
 return {'health':'unknown','stage':'verification','reasonCode':'post-update-not-verified'}
