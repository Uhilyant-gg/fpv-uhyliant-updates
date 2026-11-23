from zero_config_scenario import evaluate_zero_config_scenario

def test_missing_stages_are_deterministic(): assert evaluate_zero_config_scenario({'discovery':True})['missingStages']==['camera','video']
def test_success_is_software_only():
 r=evaluate_zero_config_scenario({'discovery':True,'camera':True,'video':True})
 assert r['ok'] is True and r['physicalEvidence'] is False
