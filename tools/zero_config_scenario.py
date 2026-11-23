"""Machine-readable software-only validation for the zero-config journey."""
from typing import Any, Mapping
_STAGES=('discovery','camera','video','operate')

def evaluate_zero_config_scenario(value: Mapping[str,Any] | None)->dict[str,Any]:
 value=value if isinstance(value,Mapping) else {}
 physical=False
 if value.get('discovery') is not True:
  return {'ok':False,'stage':'discovery','missingStages':['discovery','camera','video','operate'],'reasonCode':'discovery-unavailable','nextBestAction':'find-camera','physicalEvidence':physical}
 if value.get('cameraAmbiguous') is True:
  return {'ok':False,'stage':'camera','missingStages':['camera','video','operate'],'reasonCode':'camera-selection-ambiguous','nextBestAction':None,'physicalEvidence':physical}
 if value.get('verifiedCamera') is not True:
  return {'ok':False,'stage':'camera','missingStages':['camera','video','operate'],'reasonCode':'verified-camera-required','nextBestAction':'verify-camera','physicalEvidence':physical}
 if value.get('freshPlayback') is not True:
  action='reconnect-video' if value.get('videoState') in ('stalled','error','reconnecting','ready') else 'show-video'
  return {'ok':False,'stage':'video','missingStages':['video','operate'],'reasonCode':'fresh-playback-required','nextBestAction':action,'physicalEvidence':physical}
 if value.get('runtimeHealthy') is not True:
  return {'ok':False,'stage':'operate','missingStages':['operate'],'reasonCode':'runtime-health-required','nextBestAction':'diagnose','physicalEvidence':physical}
 return {'ok':True,'stage':'operate','missingStages':[],'reasonCode':'scenario-complete','nextBestAction':None,'physicalEvidence':physical}
