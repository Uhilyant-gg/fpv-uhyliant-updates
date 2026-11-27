from diagnostic_remediation_loop import diagnostic_remediation_loop

FINDING = {'state': 'problem', 'remediationKind': 'non-destructive'}


def test_destructive_is_service_mode():
    assert (
        diagnostic_remediation_loop({'remediationKind': 'fullflash'}, True, {'state': 'ready', 'fresh': True})[
            'reasonCode'
        ]
        == 'service-mode-required'
    )


def test_execution_without_revalidation_unknown():
    assert diagnostic_remediation_loop(FINDING, True, None)['health'] == 'unknown'


def test_stale_revalidation_is_not_ready():
    result = diagnostic_remediation_loop(FINDING, True, {'state': 'ready'})
    assert result['health'] == 'unknown' and result['reasonCode'] == 'fresh-revalidation-required'


def test_unchanged_finding_not_ready():
    assert diagnostic_remediation_loop(FINDING, True, {'state': 'problem', 'fresh': True})['health'] == 'attention'


def test_ready_only_after_revalidation():
    assert diagnostic_remediation_loop(FINDING, True, {'state': 'ready', 'fresh': True})['health'] == 'ready'
