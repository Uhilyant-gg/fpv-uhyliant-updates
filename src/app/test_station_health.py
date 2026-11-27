import unittest

from station_health import station_health
from unified_health import (
    HEALTH_ATTENTION,
    HEALTH_PROBLEM,
    HEALTH_READY,
    HEALTH_UNKNOWN,
    health_evidence,
)


class StationHealthTests(unittest.TestCase):
    def item(self, name, health, actions=()):
        return health_evidence(
            state=name,
            health=health,
            summary=f"{name} health.",
            reason_code=f"{name}-{health}",
            evidence={"component": name},
            safe_actions=actions,
        )

    def test_no_component_evidence_is_unknown(self):
        result = station_health([])
        self.assertEqual(result.health, HEALTH_UNKNOWN)
        self.assertEqual(result.reasonCode, "insufficient-evidence")

    def test_every_component_must_be_ready_before_station_is_ready(self):
        result = station_health(
            [
                self.item("camera", HEALTH_READY),
                self.item("vehicle", HEALTH_READY),
            ]
        )
        self.assertEqual(result.health, HEALTH_READY)
        self.assertEqual(result.reasonCode, "all-components-ready")

    def test_unknown_component_prevents_ready(self):
        result = station_health(
            [
                self.item("camera", HEALTH_READY),
                self.item("vehicle", HEALTH_UNKNOWN),
            ]
        )
        self.assertEqual(result.health, HEALTH_UNKNOWN)
        self.assertEqual(result.reasonCode, "component-unknown")

    def test_problem_dominates_station_health(self):
        result = station_health(
            [
                self.item("camera", HEALTH_UNKNOWN),
                self.item("vehicle", HEALTH_PROBLEM, ("diagnose",)),
            ]
        )
        self.assertEqual(result.health, HEALTH_PROBLEM)
        self.assertEqual(result.reasonCode, "component-problem")

    def test_attention_prevents_ready(self):
        result = station_health(
            [
                self.item("camera", HEALTH_READY),
                self.item("vehicle", HEALTH_ATTENTION),
            ]
        )
        self.assertEqual(result.health, HEALTH_ATTENTION)
        self.assertEqual(result.reasonCode, "component-attention")

    def test_station_boundary_does_not_infer_or_promote_safe_actions(self):
        result = station_health(
            [
                self.item("camera", HEALTH_PROBLEM, ("diagnose",)),
            ]
        )
        self.assertEqual(result.safeActions, ())
        self.assertEqual(result.evidence["components"][0]["safeActions"], ["diagnose"])


if __name__ == "__main__":
    unittest.main()
