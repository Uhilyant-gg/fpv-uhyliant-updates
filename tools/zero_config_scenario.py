"""Machine-readable software-only validation for discovery -> camera -> video."""
from typing import Any, Mapping
_STAGES=('discovery','camera','video')
def evaluate_zero_config_scenario(value: Mapping[str,Any] | None)->dict[str,Any]:
 value=value if isinstance(value,Mapping) else {}
 missing=[s for s in _STAGES if value.get(s) is not True]
 return {'ok':not missing,'missingStages':missing,'reasonCode':'scenario-complete' if not missing else 'scenario-incomplete','physicalEvidence':False}
