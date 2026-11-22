import json
import tempfile
import unittest
from pathlib import Path

from project_state import load_project_state


class ProjectStateTests(unittest.TestCase):
    def test_repository_state_is_valid(self):
        state = load_project_state()
        self.assertEqual(state["hardwareValidation"]["status"], "DEFERRED")
        self.assertFalse(state["hardwareValidation"]["physicalEvidenceComplete"])
        self.assertEqual(state["softwareTrack"]["status"], "READY")
        self.assertEqual(state["softwareTrack"]["nextMilestone"], "E5")

    def test_deferred_hardware_cannot_claim_physical_success(self):
        state = load_project_state()
        state["hardwareValidation"]["physicalEvidenceComplete"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "deferred-hardware-evidence"):
                load_project_state(path)

    def test_unknown_capability_status_fails_closed(self):
        state = load_project_state()
        state["capabilities"]["projectDoctor"] = "maybe"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "capability-status:projectDoctor"):
                load_project_state(path)


if __name__ == "__main__":
    unittest.main()
