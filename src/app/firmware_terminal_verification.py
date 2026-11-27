"""Terminal post-update verification requires fresh evidence from one matching camera."""

from typing import Any, Mapping


def firmware_terminal_verification(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return {'health': 'unknown', 'verified': False, 'reasonCode': 'terminal-evidence-unavailable'}
    if after.get('fresh') is not True or after.get('verifiedOpenIPC') is not True:
        return {'health': 'unknown', 'verified': False, 'reasonCode': 'fresh-openipc-evidence-required'}
    if any(not str(before.get(k) or '').strip() or before.get(k) != after.get(k) for k in ('platform', 'sensor')):
        return {'health': 'problem', 'verified': False, 'reasonCode': 'hardware-identity-mismatch'}
    firmware = str(after.get('firmware') or '').strip()
    if not firmware:
        return {'health': 'unknown', 'verified': False, 'reasonCode': 'observed-firmware-missing'}
    return {
        'health': 'ready',
        'verified': True,
        'observedFirmware': firmware,
        'physicalEvidence': False,
        'reasonCode': 'terminal-software-verification-complete',
    }
