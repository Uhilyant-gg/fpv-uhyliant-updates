import json
import tempfile
import unittest
from pathlib import Path
from orchestrator_state import PersistedState,evaluate,load_evidence,load_state,save_state
from orchestrator_v2 import GitHubEvidence,State

class PersistedOrchestratorStateTests(unittest.TestCase):
    def setUp(self):
        self.state=PersistedState(1,State.CI_RUNNING,"ORCH-S3","base",29,"head",0,2)
        self.evidence=GitHubEvidence(29,"head","base","ORCH-S3",True,True,True,"head","head",None)

    def test_atomic_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json"; save_state(p,self.state); self.assertEqual(load_state(p),self.state)

    def test_unknown_state_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json"; data={"schema_version":1,"state":"CI_RUNNING","story_id":"ORCH-S3","baseline_sha":"base","pr":29,"expected_head_sha":"head","unexpected":True}; p.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaises(ValueError):load_state(p)

    def test_exact_evidence_schema_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"evidence.json"; data=self.evidence.__dict__.copy(); data.pop("tested_sha"); p.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaises(ValueError):load_evidence(p)

    def test_green_exact_evidence_reconciles_and_allows_merge(self):
        result=evaluate(self.state,self.evidence,"green")
        self.assertEqual(result["state"],"REVIEWING"); self.assertTrue(result["mergeEligible"])

    def test_changed_head_fails_closed(self):
        evidence=GitHubEvidence(29,"new","base","ORCH-S3",True,True,True,"new","new",None)
        result=evaluate(self.state,evidence,"green")
        self.assertEqual(result["state"],"STATE_INCONSISTENT"); self.assertFalse(result["mergeEligible"])

    def test_missing_review_evidence_never_merges(self):
        evidence=GitHubEvidence(29,"head","base","ORCH-S3",True,True,False,"","head",None)
        result=evaluate(self.state,evidence,"green"); self.assertFalse(result["mergeEligible"])

if __name__=="__main__":unittest.main()
