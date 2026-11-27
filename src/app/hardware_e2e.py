"""Fail-closed readiness gate for physical OpenIPC end-to-end validation."""

from copy import deepcopy
import ipaddress


def _valid_sha(value):
    value = str(value or '').strip().lower()
    return len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _private_host(value):
    try:
        address = ipaddress.ip_address(str(value or '').strip())
        return (
            address.version == 4
            and address.is_private
            and not (address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified)
        )
    except ValueError:
        return False


def hardware_e2e_readiness(device, network_evidence, credentials_present=False, host_key_accepted=False, firmware=None):
    device = dict(device or {})
    identity = dict(device.get('openipcIdentity') or {})
    host = str(device.get('host') or '').strip()
    evidence = network_evidence if isinstance(network_evidence, dict) else {}
    observed = next(
        (x for x in evidence.get('devices', []) if isinstance(x, dict) and str(x.get('host') or '').strip() == host), {}
    )
    firmware = dict(firmware or {})
    artifact = dict(firmware.get('artifact') or {})
    plan = dict(firmware.get('plan') or {})
    approval = dict(firmware.get('approval') or {})
    platform = str(identity.get('platform') or '').strip().lower()
    sensor = str(identity.get('sensor') or '').strip().lower()
    profile = str(plan.get('profile') or '')
    mode = str(plan.get('mode') or '')
    token = str(plan.get('approvalToken') or '')
    sha = str(artifact.get('sha256') or '').strip().lower()
    size = artifact.get('size')
    artifact_ok = artifact.get('verified') is True and _valid_sha(sha) and type(size) is int and size > 0
    binding_ok = bool(
        plan.get('ready') is True
        and approval.get('ready') is True
        and device.get('id')
        and plan.get('deviceId') == device.get('id') == approval.get('deviceId')
        and profile
        and profile == approval.get('profile')
        and mode == 'upgrade'
        and approval.get('mode') == mode
        and token
        and token == approval.get('approvalToken')
        and plan.get('artifactSha256') == approval.get('artifactSha256') == sha
        and plan.get('artifactSize') == size
    )
    checks = {
        'deviceSelected': bool(device.get('id') and _private_host(host)),
        'openipcVerified': identity.get('verified') is True and bool(identity.get('evidence')),
        'hardwareIdentityObserved': bool(platform and sensor),
        'networkRouteObserved': bool((evidence.get('summary') or {}).get('safeRoutes', 0) > 0),
        'deviceReachableObserved': observed.get('reachable') is True,
        'firmwareArtifactVerified': artifact_ok,
        'executionPlanReady': binding_ok,
        'credentialsPresent': credentials_present is True,
        'hostKeyAccepted': host_key_accepted is True,
    }
    ready = all(checks.values())
    missing = [name for name, value in checks.items() if not value]
    return {
        'ready': ready,
        'checks': deepcopy(checks),
        'missing': missing,
        'deviceId': device.get('id') or None,
        'host': host or None,
        'platform': platform or None,
        'sensor': sensor or None,
        'firmware': identity.get('firmware') or None,
        'artifact': {'sha256': sha or None, 'size': size or None, 'build': artifact.get('build') or None},
        'profile': profile or None,
        'mode': mode or None,
        'approvalToken': token or None,
    }
