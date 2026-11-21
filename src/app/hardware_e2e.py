"""Fail-closed readiness gate for physical OpenIPC end-to-end validation."""
from copy import deepcopy


def hardware_e2e_readiness(device, network_evidence, credentials_present=False, host_key_accepted=False):
    device=dict(device or {});identity=dict(device.get('openipcIdentity') or {})
    host=str(device.get('host') or '')
    evidence=network_evidence or {};observed=next((x for x in evidence.get('devices',[]) if x.get('host')==host),{})
    checks={
        'deviceSelected':bool(device.get('id') and host),
        'openipcVerified':identity.get('verified') is True and bool(identity.get('evidence')),
        'hardwareIdentityObserved':bool(identity.get('platform') and identity.get('sensor')),
        'networkRouteObserved':bool((evidence.get('summary') or {}).get('safeRoutes',0)>0),
        'deviceReachableObserved':observed.get('reachable') is True,
        'credentialsPresent':credentials_present is True,
        'hostKeyAccepted':host_key_accepted is True,
    }
    ready=all(checks.values())
    missing=[name for name,value in checks.items() if not value]
    return {'ready':ready,'checks':deepcopy(checks),'missing':missing,'host':host or None,'platform':identity.get('platform') or None,'sensor':identity.get('sensor') or None,'firmware':identity.get('firmware') or None}
