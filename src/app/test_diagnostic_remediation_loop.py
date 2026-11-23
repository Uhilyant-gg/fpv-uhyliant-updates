from diagnostic_remediation_loop import diagnostic_remediation_loop

def test_destructive_is_service_mode(): assert diagnostic_remediation_loop({'remediationKind':'fullflash'},True,{'state':'ready'})['reasonCode']=='service-mode-required'
def test_execution_without_revalidation_unknown(): assert diagnostic_remediation_loop({'state':'problem','remediationKind':'non-destructive'},True,None)['health']=='unknown'
def test_unchanged_finding_not_ready(): assert diagnostic_remediation_loop({'state':'problem','remediationKind':'non-destructive'},True,{'state':'problem'})['health']=='attention'
def test_ready_only_after_revalidation(): assert diagnostic_remediation_loop({'state':'problem','remediationKind':'non-destructive'},True,{'state':'ready'})['health']=='ready'
