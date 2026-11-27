"""Compose deterministic non-destructive remediation with fresh revalidation."""

from typing import Any, Mapping
from remediation_revalidation import remediation_revalidation


def diagnostic_remediation_loop(
    finding: Mapping[str, Any] | None, remediation_ok: bool, after: Mapping[str, Any] | None
) -> dict[str, Any]:
    if not isinstance(finding, Mapping):
        return {'health': 'unknown', 'reasonCode': 'finding-unavailable'}
    if finding.get('remediationKind') != 'non-destructive':
        return {'health': 'attention', 'reasonCode': 'service-mode-required'}
    result = remediation_revalidation(finding, after, remediation_ok)
    return {**result, 'action': None if result['health'] == 'ready' else 'diagnose'}
