"""Evidence summary for bounded post-update lifecycle; never substitutes for physical E0."""
from typing import Any, Mapping

def post_update_lifecycle_summary(value: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(value,Mapping): return {'health':'unknown','physicalEvidence':False,'reasonCode':'post-update-evidence-unavailable'}
 required=('rediscovered','verifiedOpenIPC','platformMatch','sensorMatch','observedFirmware')
 missing=[k for k in required if not value.get(k)]
 if missing: return {'health':'unknown','physicalEvidence':False,'missing':missing,'reasonCode':'post-update-not-verified'}
 return {'health':'ready','physicalEvidence':False,'missing':[],'reasonCode':'post-update-software-contract-satisfied'}
