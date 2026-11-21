"""Fail-closed readiness gate for physical OpenIPC end-to-end validation."""
from copy import deepcopy

def _valid_sha(value):
 value=str(value or '').strip().lower();return len(value)==64 and all(c in '0123456789abcdef' for c in value)

def hardware_e2e_readiness(device,network_evidence,credentials_present=False,host_key_accepted=False,firmware=None):
 device=dict(device or {});identity=dict(device.get('openipcIdentity') or {});host=str(device.get('host') or '');evidence=network_evidence or {};observed=next((x for x in evidence.get('devices',[]) if x.get('host')==host),{});firmware=dict(firmware or {});artifact=dict(firmware.get('artifact') or {});plan=dict(firmware.get('plan') or {});approval=dict(firmware.get('approval') or {})
 artifact_ok=artifact.get('verified') is True and _valid_sha(artifact.get('sha256')) and type(artifact.get('size')) is int and artifact.get('size')>0
 binding_ok=bool(plan.get('ready') is True and approval.get('ready') is True and plan.get('deviceId')==device.get('id') and approval.get('deviceId')==device.get('id') and plan.get('profile')==approval.get('profile') and plan.get('mode')==approval.get('mode')=='upgrade' and plan.get('approvalToken') and plan.get('approvalToken')==approval.get('approvalToken') and plan.get('artifactSha256')==approval.get('artifactSha256')==artifact.get('sha256') and plan.get('artifactSize')==artifact.get('size'))
 checks={'deviceSelected':bool(device.get('id') and host),'openipcVerified':identity.get('verified') is True and bool(identity.get('evidence')),'hardwareIdentityObserved':bool(identity.get('platform') and identity.get('sensor')),'networkRouteObserved':bool((evidence.get('summary') or {}).get('safeRoutes',0)>0),'deviceReachableObserved':observed.get('reachable') is True,'firmwareArtifactVerified':artifact_ok,'executionPlanReady':binding_ok,'credentialsPresent':credentials_present is True,'hostKeyAccepted':host_key_accepted is True}
 ready=all(checks.values());missing=[name for name,value in checks.items() if not value]
 return {'ready':ready,'checks':deepcopy(checks),'missing':missing,'deviceId':device.get('id') or None,'host':host or None,'platform':identity.get('platform') or None,'sensor':identity.get('sensor') or None,'firmware':identity.get('firmware') or None,'artifact':{'sha256':artifact.get('sha256') or None,'size':artifact.get('size') or None,'build':artifact.get('build') or None},'profile':plan.get('profile') or None,'mode':plan.get('mode') or None,'approvalToken':plan.get('approvalToken') or None}
