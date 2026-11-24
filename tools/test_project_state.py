import json
import tempfile
import unittest
from pathlib import Path

from project_state import canonical_drift_errors, derive_next_milestone, load_project_state


class ProjectStateTests(unittest.TestCase):
    def test_repository_state_is_valid(self):
        state = load_project_state()
        self.assertEqual(state["hardwareValidation"]["status"], "DEFERRED")
        self.assertFalse(state["hardwareValidation"]["physicalEvidenceComplete"])
        self.assertEqual(state["softwareTrack"]["status"], "READY")
        self.assertEqual(state["capabilities"]["scenarioDrivenCI"], "complete")
        self.assertIsNone(derive_next_milestone(state))
        self.assertIsNone(state["softwareTrack"]["nextMilestone"])

    def write_state(self, state, directory):
        path = Path(directory) / "state.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        return path

    def test_deferred_hardware_cannot_claim_physical_success(self):
        state = load_project_state()
        state["hardwareValidation"]["physicalEvidenceComplete"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_state(state, tmp)
            with self.assertRaisesRegex(ValueError, "deferred-hardware-evidence"):
                load_project_state(path, check_drift=False)

    def test_unknown_capability_status_fails_closed(self):
        state = load_project_state()
        state["capabilities"]["projectDoctor"] = "maybe"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_state(state, tmp)
            with self.assertRaisesRegex(ValueError, "capability-status:projectDoctor"):
                load_project_state(path, check_drift=False)

    def test_unknown_capability_fails_closed(self):
        state = load_project_state()
        state["capabilities"]["inventedCapability"] = "pending"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_state(state, tmp)
            with self.assertRaisesRegex(ValueError, "capabilities-unknown"):
                load_project_state(path, check_drift=False)

    def test_next_milestone_is_derived_from_capabilities(self):
        state = load_project_state()
        self.assertIsNone(derive_next_milestone(state))
        state["softwareTrack"]["nextMilestone"] = "E7"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_state(state, tmp)
            with self.assertRaisesRegex(ValueError, "next-milestone"):
                load_project_state(path, check_drift=False)

    def test_canonical_drift_fails_closed(self):
        state = load_project_state()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DELIVERY_ROADMAP.md").write_text("E0 complete", encoding="utf-8")
            (root / "PROJECT_STATE.md").write_text("Hardware complete", encoding="utf-8")
            errors = canonical_drift_errors(state, root)
            self.assertIn("roadmap-hardware-boundary", errors)
            self.assertIn("project-state-hardware-boundary", errors)


if __name__ == "__main__":
    unittest.main()
