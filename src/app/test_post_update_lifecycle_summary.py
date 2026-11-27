from post_update_lifecycle_summary import post_update_lifecycle_summary


def test_sysupgrade_alone_is_not_success():
    assert post_update_lifecycle_summary({'sysupgradeComplete': True})['health'] == 'unknown'


def test_observed_firmware_required():
    r = post_update_lifecycle_summary(
        {'rediscovered': True, 'verifiedOpenIPC': True, 'platformMatch': True, 'sensorMatch': True}
    )
    assert 'observedFirmware' in r['missing']


def test_software_contract_never_claims_physical_evidence():
    r = post_update_lifecycle_summary(
        {
            'rediscovered': True,
            'verifiedOpenIPC': True,
            'platformMatch': True,
            'sensorMatch': True,
            'observedFirmware': 'v1',
        }
    )
    assert r['health'] == 'ready' and r['physicalEvidence'] is False
