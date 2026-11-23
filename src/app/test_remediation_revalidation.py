from remediation_revalidation import remediation_revalidation

def test_failed_execution_is_problem(): assert remediation_revalidation({'state':'problem'},None,False)['health']=='problem'
def test_missing_revalidation_is_unknown(): assert remediation_revalidation({'state':'problem'},None,True)['health']=='unknown'
def test_stale_revalidation_is_unknown(): assert remediation_revalidation({'state':'problem'},{'state':'ready'},True)['reasonCode']=='fresh-revalidation-required'
def test_unchanged_fresh_finding_needs_attention(): assert remediation_revalidation({'state':'problem'},{'state':'problem','fresh':True},True)['health']=='attention'
def test_fresh_ready_revalidation_completes(): assert remediation_revalidation({'state':'problem'},{'state':'ready','fresh':True},True)['health']=='ready'
