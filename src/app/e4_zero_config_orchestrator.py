"""Evidence-gated stages for the normal zero-config startup journey."""
from typing import Any, Mapping

def e4_zero_config_orchestrator(e: Mapping[str,Any] | None)->dict[str,Any]:
 e=e if isinstance(e,Mapping) else {}
 if e.get('cameraAmbiguous'): return {'health':'attention','stage':'discover','action':None,'reasonCode':'camera-selection-ambiguous'}
 if e.get('verifiedCamera') is not True: return {'health':'unknown','stage':'discover','action':'find-camera','reasonCode':'verified-camera-required'}
 if e.get('videoPlaying') is not True: return {'health':'attention','stage':'video','action':'show-video','reasonCode':'video-playback-required'}
 if e.get('runtimeHealthy') is not True: return {'health':'attention','stage':'video','action':'reconnect-video','reasonCode':'runtime-health-required'}
 return {'health':'ready','stage':'operate','action':None,'reasonCode':'zero-config-operational'}
